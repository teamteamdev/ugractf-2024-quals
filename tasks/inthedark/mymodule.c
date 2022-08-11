#include <unistd.h>

__attribute__((constructor)) void init(void) {
	write(1, "Hello, world!\n", 14);
}
