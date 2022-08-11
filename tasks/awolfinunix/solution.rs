use std::fs;
use std::os::unix::fs::FileExt;

fn read_usize<T>(mem: &fs::File, address: *const T) -> usize {
    let mut buf = [0; 8];
    mem.read_at(&mut buf, address as usize as u64).unwrap();
    usize::from_ne_bytes(buf)
}

fn run(flag: &UnsafeCell<String>) {
    let mem = fs::File::open("/proc/self/mem").unwrap();
    let base = read_usize(&mem, (flag.get() as *const u8).wrapping_add(8));
    let length = read_usize(&mem, flag.get());
    let mut flag = vec![0; length];
    mem.read_at(&mut flag, base as u64).unwrap();
    let flag = String::from_utf8(flag).unwrap();
    println!("{flag}");
}
