# Прямо с веточки: Write-up

Открыв задание, видим абсолютно бесполезное описание и 4 файла: `mem.c`,
`main.ml`, `talk` и `forest.zip`. В первых двух находится какой-то исходный код,
в `talk` какие-то логи, а в `forest.zip` есть много файлов с именами вида
`xxxx-xxxx`. Изучать начнем с логов.

## Изучаем логи

```
ocamlopt -c mem.c
ocamlopt -o main -I +unix unix.cmxa mem.o main.ml
rm -rf *.cmx *.cmi *.cmo *.o
Writing memory dump dumps/55f86fac3000-55f86fad0000... done
Writing memory dump dumps/55f87177e000-55f87181a000... done
Writing memory dump dumps/7f9163c65000-7f9163de8000... done
Writing memory dump dumps/7f9163dec000-7f9163fec000... done
Writing memory dump dumps/7f9173ded000-7f9173df0000... done
Writing memory dump dumps/7f9173fc4000-7f9173fd1000... done
Writing memory dump dumps/7f91740b4000-7f91740b6000... done
Writing memory dump dumps/7ffc0f48f000-7ffc0f4b0000... done
Writing memory dump dumps/7ffc0f5e4000-7ffc0f5e8000... failed with code 1
Writing memory dump dumps/7ffc0f5e8000-7ffc0f5ea000... done
Map has 30 elements
addrof(m) = 0x7f9163fe7208
word size = 64; int size = 63; big endian = false
```

Из первых трех строчек узнаём, что `mem.c` и `main.ml` — всё-таки какие-то
исходные коды, которые компилируются через `ocamlopt` (компилятор в
нативный код для [`Ocaml`](https://ocaml.org/)).

Затем нам говорят, что записывается какой-то дамп памяти. Заметим, что файлы
из этих строк как раз лежат внутри `forest.zip` — значит, у нас есть артефакты
работы программы.

После этих строк нам дают информацию об отображении (map): количество элементов и его
адрес в памяти.

Ну и в последней строчке нам дают информацию о машине, на которой это всё
исполнялось.

## Изучаем код

```ocaml
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
```

В переводе на человеческий:
- Читаем строку, создаём из нее `CharMap.t`, где в качестве ключа — номер символа
  в строке, а значение — это сам символ. Затем мы видим, что мы как-то затираем
  строчку, значит, в ней было что-то полезное.
- Затем мы читаем все регионы памяти из `/proc/self/maps`, которые мы можем
  читать, и которые не ассоциированны c каким-либо файлом (`inode = 0`). Для
  каждого такого региона мы получаем его начальный и конечный адрес.
- Для каждого региона мы вызываем функцию `dumpmem`, передавая путь к файлу и
  границы региона.
- Печатаем размер и адрес `CharMap.t`.

Функции `trashify`, `dumpmem` и `addrof` определены в `mem.c` и имеют префикс
`caml_`. Присмотримся к `caml_dumpmem`:

```c
CAMLprim value caml_dumpmem(value fname, value start, value end) {
  CAMLparam3(fname, start, end);

  int err = 0;

  FILE* fptr = fopen(String_val(fname), "wb");
  if (fptr == NULL) {
    CAMLreturn(Val_int(-1));
  }

  void* ptr = (void*)Long_val(start);
  size_t size = (size_t)Long_val(end) - (size_t)Long_val(start);

  size_t readed = 0;
  while (readed < size) {
    readed += fwrite(ptr + readed, 1, size - readed, fptr);
    if (err = ferror(fptr)) {
      fclose(fptr);
      CAMLreturn(Val_int(err));
    }
  }

  if (err = fclose(fptr)) {
    CAMLreturn(Val_int(err));
  }

  CAMLreturn(Val_int(0));
}
```

Она делает довольно простую вещь: открывает файл на запись и пишет туда данные,
которые напрямую выдёргивает из памяти. Обычный дамп памяти. И его дали нам.

## Разбираем память

Адрес отображения, который нам дали, лежит внутри доступных нам регионов памяти.
То есть наша цель — восстановить значение отображения из дампа памяти. Для этого
надо понять, как данные представляются в Ocaml.

Находим страницу [Interfacing with C](https://v2.ocaml.org/manual/intfc.html)
или же [Memory representation of
values](https://dev.realworldocaml.org/runtime-memory-layout.html). Полностью
разбирать это нам не надо, достаточно понять основной принцип «либо число, либо
блок». А ещё — что все значения всегда размером в одно слово (64 бита).

В Ocaml каждое значение — это либо число, которое хранится непосредственно,
но сдвинутое на один бит, либо указатель на какой-то блок. Они отличаются
последним битом, не являющимся частью значения: `1` для чисел и `0` для указателей.

Каждый блок состоит из заголовка и вложенных значений; в заголовке указан размер
блока и его тег. При этом указатель указыает на первый элемент блока, а не на
его заголовок.

Набросаем скрипт для работы с этим всем. Сначала научимся читать память:

```python
dumpsdir = sys.argv[1]
base = int(sys.argv[2], 16)

dumps = []

for fname in os.listdir(dumpsdir):
    start, end = fname.split('-')
    start = int(start, 16)
    end = int(end, 16)
    p = Path(dumpsdir + '/' + fname)
    size = p.stat().st_size
    if start + size != end:
        print(f'warn: {start:x} + {size} = {start+size:x} != {end:x}')
        end = start + size
    f = open(p, 'rb')
    dumps.append((start, end, mmap.mmap(f.fileno(), size, prot=mmap.PROT_READ)))

def read(at):
    for start, end, m in dumps:
        if at not in range(start, end):
            continue
        addr = at - start
        bytes_ = m[addr:addr+8]
        return struct.unpack('Q', bytes_)[0]
    return None
```

Затем напишем несколько вспомогательных функций:

```python
def is_block(value):
    return (value & 1) == 0

def as_int(value):
    if is_block(value):
        raise ValueError(f"value at {at} is block")
    return value >> 1

def as_block(value):
    if not is_block(value):
        raise ValueError(f"value at {at} is not block")
    return block(value)

def block(value):
    header = read(value - 8)
    tag = header & 255
    size = header >> 10
    return size, tag

def field(value, n):
    return read(value + n * 8)
```

> Фактически их реализацию можно забрать из
[`mlvalues.h`](https://github.com/ocaml/ocaml/blob/trunk/runtime/caml/mlvalues.h).

Проверим, что адрес, который нам дали, указывает на блок:

```
~/t/treemen> python -i solve.py dumps/ 0x7f9163fe7208
warn: 7ffc0f5e4000 + 8192 = 7ffc0f5e6000 != 7ffc0f5e8000
warn: 55f87177e000 + 638947 = 55f871819fe3 != 55f87181a000
>>> is_block(base)
True
>>> as_block(base)
(5, 0)
```

Видим, что блок состоит из пяти слов и имеет тег 0. Теперь нам надо найти, как
устроена структура `CharMap.t`. Поскольку это структура из стандартной
библиотеки, мы найдем её в
[`stdlib/map.ml`](https://github.com/ocaml/ocaml/blob/trunk/stdlib/map.ml):

```ocaml
type 'a t =
    Empty
  | Node of {l:'a t; v:key; d:'a; r:'a t; h:int}
```

Если внимательно вчитаться в представление типов сумм, то перед нами как раз
блок, который указывает на `Node`: у него тег ноль и размер пять элементов.

`ChatMap.t` — это бинарное дерево поиска, следовательно, чтобы прочитать значение,
нам нужно выполнить по нему спуск. Но поскольку нам нужно достать все значения
в порядке возрастания, мы можем выполнить простейший обход: для каждого узла обойти
сначала левое поддерево, потом сам этот узел, потом правое. Реализуется это так:

```python
def left(base):
    return field(base, 0)

def right(base):
    return field(base, 3)

def value(base):
    return as_int(field(base, 2))

def key(base):
    return as_int(field(base, 1))

def traverse(value):
    if not is_block(value):
        assert as_int(value) == 0
        return []
    return [*traverse(left(value)), chr(as_int(field(value, 2))), *traverse(right(value))]
```

Запустим это из корня дерева:

```python
>>> traverse(base)
['u', 'g', 'r', 'a', '_', '0', 'f', 'u', 'n', '_', 't', 'r', '3', '3', '_', 'm', 'e', 'm','0', 'r', 'y', '_', '2', '4', '2', '0', 'e', '5', '7', '9']
```

Остаётся только склеить флаг:

```python
>>> ''.join(_)
'ugra_0fun_tr33_mem0ry_2420e579'
```

Флаг: **ugra_0fun_tr33_mem0ry_2420e579**
