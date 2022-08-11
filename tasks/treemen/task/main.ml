module CharMap = Map.Make(Int)

external dumpmem : string -> int -> int -> int = "caml_dumpmem"
external addrof : 'a -> int = "caml_addrof"
external trashify : string ref -> unit = "caml_trashify"

let line = ref ""

let () =
  line := read_line ();
  let m = Seq.fold_lefti (fun acc i ch -> CharMap.add i ch acc) CharMap.empty @@ String.to_seq !line in
  trashify line;
  let maps_strings = In_channel.with_open_text ("/proc/" ^ (string_of_int @@ Unix.getpid ()) ^ "/maps") In_channel.input_lines in
  let maps = List.filter_map (fun map_string ->
    Scanf.bscanf_opt (Scanf.Scanning.from_string map_string) "%x-%x r%_c%_c%_c %_x %_x:%_x 0" (fun rstart rend -> (rstart, rend))
  ) maps_strings in
  begin
    if Sys.file_exists "dumps" then
      Array.iter (fun name -> Sys.remove @@ "dumps/" ^ name) @@ Sys.readdir "dumps"
    else Sys.mkdir "dumps" 0o777
  end;
  List.iter (fun (rstart, rend) ->
    let fname = Printf.sprintf "dumps/%x-%x" rstart rend in
    Printf.printf "Writing memory dump %s... " fname;
    let err = dumpmem fname rstart rend in
    if err != 0 then (Printf.printf "failed with code %d\n" err)
    else (print_endline "done")
  ) maps;
  Printf.printf "Map has %d elements\n" @@ CharMap.cardinal m;
  Printf.printf "addrof(m) = 0x%x\n" @@ addrof m;
  Printf.printf "word size = %d; int size = %d; big endian = %B\n" Sys.word_size Sys.int_size Sys.big_endian;
  flush_all ();
  ()

