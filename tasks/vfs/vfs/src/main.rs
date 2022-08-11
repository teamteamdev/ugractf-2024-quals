use anyhow::{ensure, Context, Result};
use memchr::memmem;
use std::collections::VecDeque;
use std::fs::{File, OpenOptions};
use std::io::{self, Write};
use std::os::unix::fs::FileExt;
use std::path::Path;

struct FileSystemActor {
    file: File,
}

// Super block format:
// 8 bytes    | Magic, "Ugra-VFS"
// 4 bytes    | Index of first free block or 0 if full
// 4 bytes    | Index of root directory block
// 4 bytes    | Count of blocks

// Free block format:
// 4 bytes    | Next free block, 0 if the tail of the VFS starting from and including this block is free, 1 if this is the only free block

// Directory block format:
// 4 bytes    | Continuation block or 0 if this is the last one
// followed by up to 170 entries in the following format:
// 1 byte     | Type, either 'd' for directory or 'f' for regular file, or '\0' if unused
// 1 byte     | Owner UID
// 1 byte     | Permissions (bitmask, r = 0x2, w = 0x1) for other users
// 1 byte     | Unused
// 4 bytes    | Contents block index
// 16 bytes   | Null-terminated filename

// File block format:
// 4 bytes    | Continuation block if available, or negated number of bytes used in this block if last
// 4092 bytes | Content chunk

struct FileIterator<'a> {
    fs: &'a FileSystemActor,
    block_index: u32,
}

struct DirectoryIterator<'a> {
    fs: &'a FileSystemActor,
    next_block_index: u32,
    block: [u8; 4096],
    position: usize,
}

#[derive(Debug)]
struct DirectoryEntry {
    is_directory: bool,
    owner_uid: u8,
    others_can_read: bool,
    others_can_write: bool,
    contents_block_index: u32,
    filename: String,
}

struct WritableFileHandle<'a> {
    fs: &'a FileSystemActor,
    block_index: u32,
    block: [u8; 4096],
}

impl Iterator for FileIterator<'_> {
    type Item = Result<Box<[u8]>>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.block_index == 0 {
            return None;
        }

        let block = match self.fs.read_block(self.block_index) {
            Ok(block) => block,
            Err(error) => return Some(Err(error.context("while reading file chunk"))),
        };
        let link = i32::from_le_bytes(*block.first_chunk::<4>().unwrap());
        let chunk = if link <= 0 {
            self.block_index = 0;
            &block[4..][..(-link) as usize]
        } else {
            self.block_index = link as u32;
            &block[4..]
        };
        Some(Ok(chunk.into()))
    }
}

impl Iterator for DirectoryIterator<'_> {
    type Item = Result<DirectoryEntry>;

    fn next(&mut self) -> Option<Self::Item> {
        loop {
            if self.position + 24 > 4096 {
                if self.next_block_index == 0 {
                    return None;
                }
                self.block = match self.fs.read_block(self.next_block_index) {
                    Ok(block) => block,
                    Err(error) => return Some(Err(error.context("while reading directory chunk"))),
                };
                self.next_block_index = u32::from_le_bytes(*self.block.first_chunk::<4>().unwrap());
                self.position = 4;
            }

            let buf = &self.block[self.position..][..24];
            self.position += 24;

            if buf[0] != 0 {
                return Some(Ok(DirectoryEntry {
                    is_directory: buf[0] == b'd',
                    owner_uid: buf[1],
                    others_can_read: buf[2] & 0x2 == 0x2,
                    others_can_write: buf[2] & 0x1 == 0x1,
                    contents_block_index: u32::from_le_bytes(*buf[4..].first_chunk::<4>().unwrap()),
                    filename: match std::str::from_utf8(&buf[8..]) {
                        Ok(filename) => filename.trim_end_matches('\0').to_string(),
                        Err(error) => {
                            return Some(
                                Err(error).context("while parsing filename in directory entry"),
                            )
                        }
                    },
                }));
            }
        }
    }
}

impl DirectoryEntry {
    fn check_can_read(&self, uid: u8) -> Result<()> {
        ensure!(
            uid == 0 || self.owner_uid == uid || self.others_can_read,
            "Permission denied"
        );
        Ok(())
    }
}

impl Write for WritableFileHandle<'_> {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        if buf.is_empty() {
            return Ok(0);
        }

        let mut bytes_filled =
            -i32::from_le_bytes(*self.block.first_chunk::<4>().unwrap()) as usize;

        if bytes_filled == 4092 {
            match self.fs.alloc_block() {
                Ok(new_block_index) => {
                    self.block[..4].copy_from_slice(&new_block_index.to_le_bytes());
                    if let Err(error) = self
                        .fs
                        .write_block(self.block_index, self.block)
                        .context("while flushing full block")
                    {
                        return Err(io::Error::other(error));
                    }
                    self.block_index = new_block_index;
                    self.block = [0u8; 4096];
                    bytes_filled = 0;
                }
                Err(error) => {
                    return Err(io::Error::other(
                        error.context("while allocating new block"),
                    ))
                }
            }
        }

        let bytes_to_copy = buf.len().min((4092 - bytes_filled) as usize);
        self.block[4 + bytes_filled..4 + bytes_filled + bytes_to_copy]
            .copy_from_slice(&buf[..bytes_to_copy]);
        self.block[..4].copy_from_slice(&(-((bytes_filled + bytes_to_copy) as i32)).to_le_bytes());
        Ok(bytes_to_copy)
    }

    fn flush(&mut self) -> io::Result<()> {
        if let Err(error) = self
            .fs
            .write_block(self.block_index, self.block)
            .context("while flushing block")
        {
            return Err(io::Error::other(error));
        }
        Ok(())
    }
}

impl Drop for WritableFileHandle<'_> {
    fn drop(&mut self) {
        self.flush().expect("Failed to flush");
    }
}

impl FileSystemActor {
    fn new(path: &Path) -> Result<Self> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(path)
            .context("while opening VFS file")?;
        if file
            .metadata()
            .context("while retrieving file metadata")?
            .len()
            == 0
        {
            const LENGTH: u64 = 15 * 1024 * 1024;
            file.set_len(LENGTH).context("while setting VFS size")?;
            let mut super_block = [0u8; 4096];
            super_block[..8].copy_from_slice(b"Ugra-VFS");
            super_block[8..12].copy_from_slice(&2u32.to_le_bytes());
            super_block[12..16].copy_from_slice(&1u32.to_le_bytes());
            super_block[16..20].copy_from_slice(&((LENGTH / 4096) as u32).to_le_bytes());
            file.write_all_at(&super_block, 0)
                .context("while initializing super block")?;
        }
        Ok(Self { file })
    }

    fn remove_last_path_component(path: &str) -> Result<(&str, &str)> {
        let (mut dir_path, filename) = path.rsplit_once('/').context("Invalid path")?;
        if dir_path == "" {
            dir_path = "/";
        }
        Ok((dir_path, filename))
    }

    fn read_block(&self, index: u32) -> Result<[u8; 4096]> {
        let mut block = [0u8; 4096];
        self.file
            .read_exact_at(&mut block, (index as u64) * 4096)
            .with_context(|| format!("while reading block {index}"))?;
        Ok(block)
    }

    fn write_block(&self, index: u32, block: [u8; 4096]) -> Result<()> {
        self.file
            .write_all_at(&block, (index as u64) * 4096)
            .with_context(|| format!("while writing block {index}"))
    }

    fn get_root_block_index(&self) -> Result<u32> {
        let super_block = self.read_block(0).context("while reading super block")?;
        Ok(u32::from_le_bytes(
            *super_block[12..].first_chunk::<4>().unwrap(),
        ))
    }

    fn alloc_block(&self) -> Result<u32> {
        let mut super_block = self.read_block(0).context("while reading super block")?;
        let free_block_index = u32::from_le_bytes(*super_block[8..].first_chunk::<4>().unwrap());
        ensure!(free_block_index != 0, "Disk full");
        let free_block = self
            .read_block(free_block_index)
            .context("while reading free block")?;
        let mut next_free_block_index = u32::from_le_bytes(*free_block.first_chunk::<4>().unwrap());
        if next_free_block_index == 0 {
            next_free_block_index = free_block_index + 1;
            let total_blocks = u32::from_le_bytes(*super_block[16..].first_chunk::<4>().unwrap());
            if next_free_block_index == total_blocks {
                next_free_block_index = 0;
            }
        } else if next_free_block_index == 1 {
            next_free_block_index = 0;
        }
        super_block[8..12].copy_from_slice(&next_free_block_index.to_le_bytes());
        self.write_block(0, super_block)
            .context("while writing super block")?;
        Ok(free_block_index)
    }

    fn free_block(&self, block_index: u32) -> Result<()> {
        let mut super_block = self.read_block(0).context("while reading super block")?;
        let free_block_index = u32::from_le_bytes(*super_block[8..].first_chunk::<4>().unwrap());
        let mut block = [0u8; 4096];
        block[..4].copy_from_slice(
            &if free_block_index == 0 {
                1
            } else {
                free_block_index
            }
            .to_le_bytes(),
        );
        self.write_block(block_index, block)
            .context("while updating list in free block")?;
        super_block[8..12].copy_from_slice(&block_index.to_le_bytes());
        self.write_block(0, super_block)
            .context("while writing super block")?;
        Ok(())
    }

    fn count_free_blocks(&self) -> Result<u32> {
        let super_block = self.read_block(0).context("while reading super block")?;
        let mut free_block_index =
            u32::from_le_bytes(*super_block[8..].first_chunk::<4>().unwrap());
        let mut count = 0;
        while free_block_index != 0 {
            count += 1;
            let free_block = self
                .read_block(free_block_index)
                .context("while reading free block")?;
            let mut next_free_block_index =
                u32::from_le_bytes(*free_block.first_chunk::<4>().unwrap());
            if next_free_block_index == 0 {
                let total_blocks =
                    u32::from_le_bytes(*super_block[16..].first_chunk::<4>().unwrap());
                count += total_blocks - free_block_index - 1;
            } else if next_free_block_index == 1 {
                next_free_block_index = 0;
            }
            free_block_index = next_free_block_index;
        }
        Ok(count)
    }

    fn traverse_path(&self, path: &str, uid: u8) -> Result<DirectoryEntry> {
        ensure!(path.starts_with("/"), "Path must start with /");

        let mut entry = DirectoryEntry {
            is_directory: true,
            owner_uid: 0,
            others_can_read: true,
            others_can_write: false,
            contents_block_index: self
                .get_root_block_index()
                .context("while retrieving root block index")?,
            filename: "/".to_string(),
        };
        if path == "/" {
            return Ok(entry);
        }

        for filename in path[1..].split('/') {
            ensure!(
                entry.is_directory,
                "Traversing past a regular file is not allowed",
            );
            ensure!(
                uid == 0 || entry.owner_uid == uid || entry.others_can_read,
                "Permission denied while entering directory"
            );
            ensure!(!filename.is_empty(), "Filename cannot be empty");
            ensure!(
                filename.len() <= 16,
                "Filename cannot be longer than 16 bytes",
            );

            let mut found = false;
            for child_entry in self.read_directory_by_block(entry.contents_block_index) {
                let child_entry = child_entry.context("while traversing directory tree")?;
                if child_entry.filename != filename {
                    continue;
                }
                entry = child_entry;
                found = true;
                break;
            }
            ensure!(found, "Not found");
        }

        Ok(entry)
    }

    fn read_file<'a>(
        &'a self,
        path: &str,
        uid: u8,
    ) -> Result<impl Iterator<Item = Result<Box<[u8]>>> + 'a> {
        let entry = self.traverse_path(path, uid)?;
        ensure!(
            !entry.is_directory,
            "Expected a regular file, not a directory",
        );
        ensure!(
            uid == 0 || entry.owner_uid == uid || entry.others_can_read,
            "Permission denied while reading file",
        );
        Ok(self.read_file_by_block(entry.contents_block_index))
    }

    fn read_file_by_block<'a>(
        &'a self,
        block_index: u32,
    ) -> impl Iterator<Item = Result<Box<[u8]>>> + 'a {
        FileIterator {
            fs: self,
            block_index,
        }
    }

    fn write_file<'a>(
        &'a self,
        path: &str,
        uid: u8,
        mode_if_new: u8,
        uid_if_new: u8,
    ) -> Result<WritableFileHandle> {
        ensure!(path != "/", "Expected a regular file, not a directory");
        let (dir_path, filename) =
            Self::remove_last_path_component(path).context("Invalid path")?;
        let dir_entry = self.traverse_path(dir_path, uid)?;
        ensure!(
            dir_entry.is_directory,
            "Traversing past a regular file is not allowed",
        );
        ensure!(
            uid == 0 || dir_entry.owner_uid == uid || dir_entry.others_can_read,
            "Permission denied while entering directory",
        );
        let mut file_entry = None;
        for entry in self.read_directory_by_block(dir_entry.contents_block_index) {
            let entry = entry.context("while traversing directory tree")?;
            if entry.filename == filename {
                file_entry = Some(entry);
                break;
            }
        }
        let file_first_block = match file_entry {
            Some(file_entry) => {
                ensure!(!file_entry.is_directory, "Cannot write over a directory");
                self.erase_object_by_block(file_entry.contents_block_index)
                    .context("while erasing file")?;
                file_entry.contents_block_index
            }
            None => {
                ensure!(
                    uid == 0 || dir_entry.owner_uid == uid || dir_entry.others_can_write,
                    "Permission denied while creating file",
                );
                self.create_new_object_in_directory_by_block(
                    dir_entry.contents_block_index,
                    filename,
                    false,
                    uid_if_new,
                    mode_if_new,
                )
                .context("while creating file")?
            }
        };
        Ok(WritableFileHandle {
            fs: self,
            block_index: file_first_block,
            block: [0u8; 4096],
        })
    }

    fn erase_object_by_block(&self, first_block_index: u32) -> Result<()> {
        let mut block = self
            .read_block(first_block_index)
            .context("while reading first block")?;
        self.write_block(first_block_index, [0u8; 4096])
            .context("while erasing first block")?;
        let mut block_index = i32::from_le_bytes(*block.first_chunk::<4>().unwrap());
        while block_index > 0 {
            block = self.read_block(block_index as u32)?;
            self.free_block(block_index as u32)?;
            block_index = i32::from_le_bytes(*block.first_chunk::<4>().unwrap());
        }
        Ok(())
    }

    fn read_directory<'a>(
        &'a self,
        path: &str,
        uid: u8,
    ) -> Result<impl Iterator<Item = Result<DirectoryEntry>> + 'a> {
        let entry = self.traverse_path(path, uid)?;
        ensure!(
            entry.is_directory,
            "Expected a directory, not a regular file"
        );
        ensure!(
            uid == 0 || entry.owner_uid == uid || entry.others_can_read,
            "Permission denied while reading directory",
        );
        Ok(self.read_directory_by_block(entry.contents_block_index))
    }

    fn read_directory_by_block<'a>(
        &'a self,
        block_index: u32,
    ) -> impl Iterator<Item = Result<DirectoryEntry>> + 'a {
        DirectoryIterator {
            fs: self,
            next_block_index: block_index,
            block: [0u8; 4096],
            position: 4096,
        }
    }

    fn create_directory<'a>(
        &'a self,
        path: &str,
        uid: u8,
        mode_if_new: u8,
        uid_if_new: u8,
    ) -> Result<()> {
        ensure!(path != "/", "Path already exists");
        let (dir_path, filename) =
            Self::remove_last_path_component(path).context("Invalid path")?;
        let dir_entry = self.traverse_path(dir_path, uid)?;
        ensure!(
            dir_entry.is_directory,
            "Traversing past a regular file is not allowed",
        );
        ensure!(
            uid == 0 || dir_entry.owner_uid == uid || dir_entry.others_can_read,
            "Permission denied while entering directory",
        );
        for entry in self.read_directory_by_block(dir_entry.contents_block_index) {
            let entry = entry.context("while traversing directory tree")?;
            ensure!(entry.filename != filename, "Path already exists");
        }
        ensure!(
            uid == 0 || dir_entry.owner_uid == uid || dir_entry.others_can_write,
            "Permission denied while creating file",
        );
        self.create_new_object_in_directory_by_block(
            dir_entry.contents_block_index,
            filename,
            true,
            uid_if_new,
            mode_if_new,
        )
        .context("while creating directory")?;
        Ok(())
    }

    fn create_new_object_in_directory_by_block(
        &self,
        mut directory_block_index: u32,
        filename: &str,
        is_directory: bool,
        uid: u8,
        mode: u8,
    ) -> Result<u32> {
        ensure!(!filename.is_empty(), "Filename cannot be empty");
        ensure!(
            filename.len() <= 16,
            "Filename cannot be longer than 16 bytes",
        );
        let mut filename_buf = [0u8; 16];
        filename_buf[..filename.len()].copy_from_slice(filename.as_bytes());

        let contents_block_index = self
            .alloc_block()
            .context("while allocating block for object")?;
        self.write_block(contents_block_index, [0u8; 4096])
            .context("while cleaning object block")?;

        let mut directory_block = self
            .read_block(directory_block_index)
            .context("while reading directory")?;

        loop {
            let mut position = 4;
            while position + 24 <= 4096 {
                let buf = &mut directory_block[position..][..24];
                if buf[0] != 0 {
                    position += 24;
                    continue;
                }
                buf[0] = if is_directory { b'd' } else { b'f' };
                buf[1] = uid;
                buf[2] = mode;
                buf[4..8].copy_from_slice(&contents_block_index.to_le_bytes());
                buf[8..24].copy_from_slice(&filename_buf);
                self.write_block(directory_block_index, directory_block)
                    .context("while writing directory")?;
                return Ok(contents_block_index);
            }

            let mut next_directory_block_index =
                u32::from_le_bytes(*directory_block.first_chunk::<4>().unwrap());
            if next_directory_block_index == 0 {
                next_directory_block_index = self
                    .alloc_block()
                    .context("while allocating block for directory entries")?;
                directory_block[..4].copy_from_slice(&next_directory_block_index.to_le_bytes());
                self.write_block(directory_block_index, directory_block)
                    .context("writing writing directory")?;
                directory_block = [0u8; 4096];
            } else {
                directory_block = self
                    .read_block(directory_block_index)
                    .context("while reading directory")?;
            }
            directory_block_index = next_directory_block_index;
        }
    }

    fn unlink(&self, path: &str, uid: u8) -> Result<()> {
        ensure!(path != "/", "Cannot unlink root directory");
        let (dir_path, filename) =
            Self::remove_last_path_component(path).context("Invalid path")?;
        let dir_entry = self.traverse_path(dir_path, uid)?;
        ensure!(
            dir_entry.is_directory,
            "Traversing past a regular file is not allowed",
        );
        ensure!(
            uid == 0 || dir_entry.owner_uid == uid || dir_entry.others_can_read,
            "Permission denied while entering directory",
        );

        ensure!(!filename.is_empty(), "Filename cannot be empty");
        ensure!(
            filename.len() <= 16,
            "Filename cannot be longer than 16 bytes",
        );
        let mut filename_buf = [0u8; 16];
        filename_buf[..filename.len()].copy_from_slice(filename.as_bytes());

        let mut prev_directory_block_index = 0;
        let mut prev_directory_block = [0u8; 4096];
        let mut directory_block_index = dir_entry.contents_block_index;

        loop {
            let mut directory_block = self
                .read_block(directory_block_index)
                .context("while reading directory")?;

            let mut position = 4;
            while position + 24 <= 4096 {
                let buf = &mut directory_block[position..][..24];
                if buf[0] == 0 || buf[8..24] != filename_buf {
                    position += 24;
                    continue;
                }
                ensure!(
                    uid == 0 || dir_entry.owner_uid == uid || dir_entry.others_can_write,
                    "Permission denied while deleting file",
                );
                let contents_block_index =
                    u32::from_le_bytes(*buf[4..].first_chunk::<4>().unwrap());
                self.erase_object_by_block(contents_block_index)
                    .context("while erasing file")?;
                self.free_block(contents_block_index)
                    .context("while freeing first block")?;
                buf[0] = 0;
                if (0..170).any(|i| directory_block[4 + 24 * i] != 0)
                    || prev_directory_block_index == 0
                {
                    self.write_block(directory_block_index, directory_block)
                        .context("while writing directory")?;
                } else {
                    prev_directory_block[..4].copy_from_slice(&directory_block[..4]);
                    self.write_block(prev_directory_block_index, prev_directory_block)
                        .context("while writing directory")?;
                    self.free_block(directory_block_index)
                        .context("while freeing empty directory block")?;
                }
                return Ok(());
            }

            prev_directory_block_index = directory_block_index;
            prev_directory_block = directory_block;
            directory_block_index =
                u32::from_le_bytes(*directory_block.first_chunk::<4>().unwrap());
            ensure!(directory_block_index != 0, "Not found");
        }
    }
}

struct Shell {
    fs: FileSystemActor,
    cwd: String,
    uid: u8,
    username: String,
}

impl Shell {
    fn repl(&mut self) -> Result<()> {
        loop {
            print!("{}$ ", self.cwd);
            io::stdout().flush().context("while flushing stdout")?;
            let mut command = String::new();
            if io::stdin()
                .read_line(&mut command)
                .context("while reading command from stdin")?
                == 0
            {
                return Ok(());
            }
            self.handle_command(&command)
                .context("while executing REPL command")?;
        }
    }

    fn get_absolute_path(&self, path: &str) -> String {
        let mut components = if path.starts_with('/') || self.cwd == "/" {
            vec![]
        } else {
            self.cwd[1..].split('/').collect()
        };
        for part in path.split('/') {
            match part {
                "" | "." => {}
                ".." => {
                    let _ = components.pop();
                }
                part => components.push(part),
            }
        }
        let mut path = String::from("");
        for part in components {
            path += "/";
            path += part;
        }
        if path.is_empty() {
            path += "/";
        }
        path
    }

    fn handle_command(&mut self, command: &str) -> Result<()> {
        let mut args = command.split_ascii_whitespace();
        let Some(name) = args.next() else {
            return Ok(());
        };
        match name {
            "help" => {
                println!("Supported commands:");
                println!("help                            Print this help");
                println!("exit                            Quit session");
                println!("resys                           Reset filesystem to backup");
                println!("cd <path>                       Change working directory");
                println!("ls [<path>]                     List files in directory");
                println!("cat <path>                      Print file contents");
                println!("stat <path>                     Print file metadata");
                println!("find [<path>]                   Recursively list directory");
                println!("grep <str> <path>               Search files for substring");
                println!("write <path> <data>             Overwrite file with hex data");
                println!("mkdir <path>                    Create directory");
                println!("unlink <path>                   Delete file/directory");
                println!("df                              Show free space");
                println!("whoami                          Show current user");
            }
            "exit" => std::process::exit(0),
            "resys" => {
                if let Err(error) = std::fs::remove_file("data/filesystem.vfs") {
                    println!("resys: {error:?}");
                    return Ok(());
                }
                println!("Reconnect now.");
                std::process::exit(0);
            }
            "cd" => {
                let Some(new_cwd) = args.next() else {
                    println!("cd: Missing argument");
                    return Ok(());
                };
                let new_cwd = self.get_absolute_path(new_cwd);
                if let Err(error) = self.fs.read_directory(&new_cwd, self.uid) {
                    println!("cd: Invalid directory: {error:?}");
                    return Ok(());
                }
                self.cwd = new_cwd.to_string();
            }
            "ls" => {
                let path = self.get_absolute_path(args.next().unwrap_or("."));
                let dir = match self.fs.read_directory(&path, self.uid) {
                    Ok(dir) => dir,
                    Err(error) => {
                        println!("ls: {error:?}");
                        return Ok(());
                    }
                };
                println!("Type  UID  Your perms  Public perms  Filename");
                for entry in dir {
                    let entry = match entry {
                        Ok(entry) => entry,
                        Err(error) => {
                            println!("ls: {error:?}");
                            return Ok(());
                        }
                    };
                    println!(
                        "{}  {:3}  {}{}          {}{}            {}",
                        if entry.is_directory { "dir " } else { "file" },
                        entry.owner_uid,
                        if entry.others_can_read || entry.owner_uid == self.uid {
                            "r"
                        } else {
                            "-"
                        },
                        if entry.others_can_write || entry.owner_uid == self.uid {
                            "w"
                        } else {
                            "-"
                        },
                        if entry.others_can_read { "r" } else { "-" },
                        if entry.others_can_write { "w" } else { "-" },
                        entry.filename,
                    );
                }
            }
            "cat" => {
                let Some(path) = args.next() else {
                    println!("cat: Missing argument");
                    return Ok(());
                };
                let path = self.get_absolute_path(path);
                let iterator = match self.fs.read_file(&path, self.uid) {
                    Ok(iterator) => iterator,
                    Err(error) => {
                        println!("cat: {error:?}");
                        return Ok(());
                    }
                };
                for chunk in iterator {
                    let chunk = match chunk {
                        Ok(chunk) => chunk,
                        Err(error) => {
                            println!("cat: {error:?}");
                            return Ok(());
                        }
                    };
                    io::stdout().write_all(&chunk)?;
                }
            }
            "stat" => {
                let Some(path) = args.next() else {
                    println!("stat: Missing argument");
                    return Ok(());
                };
                let path = self.get_absolute_path(path);
                let entry = match self.fs.traverse_path(&path, self.uid) {
                    Ok(entry) => entry,
                    Err(error) => {
                        println!("stat: {error:?}");
                        return Ok(());
                    }
                };
                println!(
                    "File type: {}",
                    if entry.is_directory {
                        "directory"
                    } else {
                        "regular file"
                    },
                );
                println!("Owner UID: {}", entry.owner_uid);
                println!(
                    "Permissions for everyone but owner: {} read, {} write",
                    if entry.others_can_read {
                        "may"
                    } else {
                        "may not"
                    },
                    if entry.others_can_write {
                        "may"
                    } else {
                        "may not"
                    },
                );
                println!("First block: {}", entry.contents_block_index);
                println!("Filename: {}", entry.filename);
            }
            "find" => {
                let path = self.get_absolute_path(args.next().unwrap_or("."));
                let entry = match self.fs.traverse_path(&path, self.uid) {
                    Ok(entry) => entry,
                    Err(error) => {
                        println!("stat: {error:?}");
                        return Ok(());
                    }
                };
                if !entry.is_directory {
                    println!("{path}");
                    return Ok(());
                }
                if let Err(error) = entry.check_can_read(self.uid) {
                    println!("find: {path}: {error:?}");
                    return Ok(());
                }
                fn walk(shell: &Shell, path: &str, contents_block_index: u32) {
                    let iterator = shell.fs.read_directory_by_block(contents_block_index);
                    for entry in iterator {
                        let entry = match entry {
                            Ok(entry) => entry,
                            Err(error) => {
                                println!("find: {path}: {error:?}");
                                return;
                            }
                        };
                        let new_path = if path == "/" {
                            format!("/{}", entry.filename)
                        } else {
                            format!("{path}/{}", entry.filename)
                        };
                        println!("{new_path}");
                        if entry.is_directory {
                            if let Err(error) = entry.check_can_read(shell.uid) {
                                println!("find: {new_path}: {error:?}");
                                return;
                            }
                            walk(shell, &new_path, entry.contents_block_index);
                        }
                    }
                }
                println!("{path}");
                walk(self, &path, entry.contents_block_index);
            }
            "grep" => {
                let Some(pattern) = args.next() else {
                    println!("grep: Missing argument");
                    return Ok(());
                };
                let Some(path) = args.next() else {
                    println!("grep: Missing argument");
                    return Ok(());
                };
                let path = self.get_absolute_path(path);
                let entry = match self.fs.traverse_path(&path, self.uid) {
                    Ok(entry) => entry,
                    Err(error) => {
                        println!("grep: {path}: {error:?}");
                        return Ok(());
                    }
                };
                if let Err(error) = entry.check_can_read(self.uid) {
                    println!("grep: {path}: {error:?}");
                    return Ok(());
                }
                fn grep(shell: &Shell, pattern: &str, path: &str, contents_block_index: u32) {
                    let mut buf = VecDeque::new();
                    let mut no_newline_until = 0;
                    let mut line_no = 1;
                    let mut handle_line = |line: Vec<u8>| {
                        if memmem::find(&line, pattern.as_bytes()).is_some() {
                            print!("{path}:{line_no}:");
                            io::stdout()
                                .write_all(&line)
                                .expect("Failed to write to stdout");
                        }
                        line_no += 1;
                    };
                    for chunk in shell.fs.read_file_by_block(contents_block_index) {
                        match chunk {
                            Ok(chunk) => buf.extend(chunk.iter()),
                            Err(error) => {
                                println!("grep: {path}: {error:?}");
                                return;
                            }
                        };
                        while no_newline_until < buf.len() {
                            while no_newline_until < buf.len() && buf[no_newline_until] != b'\n' {
                                no_newline_until += 1;
                            }
                            if no_newline_until < buf.len() {
                                let line: Vec<u8> = buf.drain(..no_newline_until + 1).collect();
                                no_newline_until = 0;
                                handle_line(line);
                            }
                        }
                    }
                    handle_line(buf.into());
                }
                fn walk(shell: &Shell, pattern: &str, path: &str, contents_block_index: u32) {
                    for entry in shell.fs.read_directory_by_block(contents_block_index) {
                        let entry = match entry {
                            Ok(entry) => entry,
                            Err(error) => {
                                println!("grep: {path}: {error:?}");
                                return;
                            }
                        };
                        let new_path = if path == "/" {
                            format!("/{}", entry.filename)
                        } else {
                            format!("{path}/{}", entry.filename)
                        };
                        if let Err(error) = entry.check_can_read(shell.uid) {
                            println!("grep: {new_path}: {error:?}");
                            continue;
                        }
                        if entry.is_directory {
                            walk(shell, pattern, &new_path, entry.contents_block_index);
                        } else {
                            grep(shell, pattern, &new_path, entry.contents_block_index);
                        }
                    }
                }
                if entry.is_directory {
                    walk(self, pattern, &path, entry.contents_block_index);
                } else {
                    grep(self, pattern, &path, entry.contents_block_index);
                }
            }
            "write" => {
                let Some(path) = args.next() else {
                    println!("write: Missing argument");
                    return Ok(());
                };
                let Some(data) = args.next() else {
                    println!("write: Missing argument");
                    return Ok(());
                };
                let data = match hex::decode(data) {
                    Ok(data) => data,
                    Err(error) => {
                        println!("write: Invalid hexadecimal data: {error:?}");
                        return Ok(());
                    }
                };
                let path = self.get_absolute_path(path);
                let mut handle = match self.fs.write_file(&path, self.uid, 0x0, self.uid) {
                    Ok(handle) => handle,
                    Err(error) => {
                        println!("write: {error:?}");
                        return Ok(());
                    }
                };
                if let Err(error) = handle.write_all(&data) {
                    println!("write: {error:?}");
                }
            }
            "mkdir" => {
                let Some(path) = args.next() else {
                    println!("mkdir: Missing argument");
                    return Ok(());
                };
                let path = self.get_absolute_path(path);
                if let Err(error) = self.fs.create_directory(&path, self.uid, 0x0, self.uid) {
                    println!("mkdir: {error:?}");
                }
            }
            "unlink" => {
                let Some(path) = args.next() else {
                    println!("unlink: Missing argument");
                    return Ok(());
                };
                let path = self.get_absolute_path(path);
                if let Err(error) = self.fs.unlink(&path, self.uid) {
                    println!("unlink: {error:?}");
                }
            }
            "df" => match self.fs.count_free_blocks() {
                Ok(blocks) => println!("{blocks} blocks left"),
                Err(error) => println!("df: {error:?}"),
            },
            "whoami" => println!("{} (UID {})", self.username, self.uid),
            _ => println!("Unknown command '{name}'. Try 'help'."),
        }
        Ok(())
    }
}

fn init_fs(fs: &FileSystemActor) -> Result<()> {
    fs.create_directory("/home", 0, 0x2, 0)?;
    fs.create_directory("/home/guest", 0, 0x2, 0x80)?;
    fs.create_directory("/home/purplesyringa", 0, 0x2, 0x81)?;
    fs.write_file("/home/purplesyringa/sticker.webp", 0x81, 0x2, 0x81)?
        .write_all(&std::fs::read("sticker.webp")?)?;
    fs.write_file("/home/purplesyringa/flag.txt", 0x81, 0x0, 0x81)?
        .write_all(std::env::var("KYZYLBORDA_SECRET_flag")?.as_bytes())?;
    fs.create_directory("/home/purplesyringa/vfs", 0x81, 0x2, 0x81)?;
    fs.write_file("/home/purplesyringa/vfs/main.rs", 0x81, 0x2, 0x81)?
        .write_all(&std::fs::read("src/main.rs")?)?;
    fs.write_file("/home/purplesyringa/vfs/vfs", 0x81, 0x2, 0x81)?
        .write_all(&std::fs::read("target/release/vfs")?)?;
    Ok(())
}

fn main() -> Result<()> {
    let fs =
        FileSystemActor::new(Path::new("data/filesystem.vfs")).context("Failed to open VFS")?;
    let _ = init_fs(&fs);

    Shell {
        fs,
        cwd: String::from("/"),
        uid: 0x80,
        username: String::from("guest"),
    }
    .repl()
}
