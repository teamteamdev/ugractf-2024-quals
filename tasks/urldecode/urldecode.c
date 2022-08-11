// c program to urldecode a string from argv[1]
// Usage: urldecode "string to decode"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const char FLAG[] = "ugra_dummy_dummy_dummy_dummy_d_123456789012";

int main(int argc, char *argv[])
{
    char hex[256];

    char flag[44];
    memcpy(flag, FLAG, 44);

    for (int i = 0; i < 8; i++)
    {
        for (int j = 0; j < 16; j++)
        {
            hex[i * 16 + j] = i * 16 + j;
        }
    }

    char *str = malloc(4096);
    if (argc != 2)
    {
        printf("Enter a string to decode\n");
        fflush(stdout);
        fgets(str, 4095, stdin);
    }
    else
    {
        int len = strlen(argv[1]) < 4096 ? strlen(argv[1]) : 4096;
        memcpy(str, argv[1], len);
    }

    char *decoded = malloc(strlen(str) + 1);
    if (decoded == NULL)
    {
        printf("Memory allocation failed\n");
        return 1;
    }

    char *d = decoded;
    // printf("Decoding: %s\n", str);
    while (*str)
    {
        if (*str == '%')
        {
            if (str[1] && str[2])
            {
                int hi = str[1];
                int lo = str[2];
                if (hi <= '9')
                {
                    hi -= '0';
                }
                else if (hi <= 'F')
                {
                    hi -= 'A' - 10;
                }
                else if (hi <= 'f')
                {
                    hi -= 'a' - 10;
                }
                else
                {
                    hi = 0;
                }

                if (lo <= '9')
                {
                    lo -= '0';
                }
                else if (lo <= 'F')
                {
                    lo -= 'A' - 10;
                }
                else if (lo <= 'f')
                {
                    lo -= 'a' - 10;
                }
                else
                {
                    lo = 0;
                }
                *d = hex[hi * 16 + lo];
                str += 2;
            }
        }
        else if (*str == '+')
        {
            *d = ' ';
        }
        else
        {
            *d = *str;
        }
        str++;
        d++;
    }
    *d = '\0';

    printf("Decoded: ");
    // print out all symbols
    for (int i = 0; i < d - decoded; i++)
    {
        putchar(decoded[i]);
    }
    putchar('\n');
    free(decoded);
    return 0;
}

// compile with:
// gcc -Wall -o urldecode urldecode.c