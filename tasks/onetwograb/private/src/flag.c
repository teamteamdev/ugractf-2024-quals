#include <stdint.h>

// https://en.wikipedia.org/wiki/Multiply-with-carry

#define PHI 0x9e3779b9

static uint32_t Q[4096], c = 362436;

void init_rand(uint32_t x) {
    int i;

    Q[0] = x;
    Q[1] = x + PHI;
    Q[2] = x + PHI + PHI;

    for (i = 3; i < 4096; i++)
        Q[i] = Q[i - 3] ^ Q[i - 2] ^ PHI ^ i;
}

uint32_t rand_cmwc(void) {
    uint64_t t, a = 18782LL;
    static uint32_t i = 4095;
    uint32_t x, r = 0xfffffffe;
    i = (i + 1) & 4095;
    t = a * Q[i] + c;
    c = (t >> 32);
    x = t + c;
    if (x < c) {
        x++;
        c++;
    }
    return (Q[i] = r - x);
}

char *flag = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX";

char *get_flag() {
    unsigned char buf[64];

    uint32_t i;
    uint32_t r;
    
    init_rand(83886608);
    for (i = 0; i < 64; ++i) buf[i] = i * 3;
    
    for (i = 0; i < 4294967295; ++i) {
        r = rand_cmwc();
        buf[(r & 0x3f0000) >> 16] ^= (r & 0xff);
    }
    
    for (i = 0; i < 64; ++i) {
        flag[i] = flag[i] ^ buf[i];
    }

    return flag;
}

uint32_t get_flag_length() {
    return 64;
}
