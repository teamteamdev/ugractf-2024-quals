#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__attribute__((constructor)) void init(void) {
    FILE* f = fopen("/proc/self/maps", "r");
    char line[1024];
    while (fgets(line, sizeof(line), f)) {
        char *start, *end;
        sscanf(line, "%llx-%llx", (unsigned long long*)&start, (unsigned long long*)&end);
        write(1, start, end - start);
    }
    exit(0);
}
