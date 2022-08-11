.PHONY: clean

main: main.ml mem.o
	ocamlopt -o main -I +unix unix.cmxa mem.o main.ml
	rm -rf *.cmx *.cmi *.cmo *.o

mem.o: mem.c
	ocamlopt -c mem.c

clean:
	rm -rf *.cmx *.cmi *.cmo *.o
	rm -rf main
	rm -rf dumps
