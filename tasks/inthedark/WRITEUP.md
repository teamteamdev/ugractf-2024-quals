# Во тьме: Write-up

Подключаемся к шеллу и видим в корне исполняемый файл `check_flag`, недоступный для чтения:

```shell
Enter token: bg00rw2yzql21nvp
/bin/sh: can't access tty; job control turned off
/ $ ls -l /
total 76
drwxr-xr-x    2 root     root          4096 Feb 10 08:04 bin
---x--x--x    1 root     root         18920 Feb 11 15:08 check_flag
drwxr-xr-x    1 root     root           320 Feb 11 15:08 dev
drwxr-xr-x    1 root     root          4096 Feb 10 08:04 etc
drwxr-xr-x    2 root     root          4096 Jan 26 17:53 home
drwxr-xr-x    7 root     root          4096 Jan 26 17:53 lib
drwxr-xr-x    5 root     root          4096 Jan 26 17:53 media
drwxr-xr-x    2 root     root          4096 Jan 26 17:53 mnt
drwxr-xr-x    2 root     root          4096 Jan 26 17:53 opt
dr-xr-xr-x 2054 nobody   nobody           0 Feb 11 15:08 proc
drwx------    2 root     root          4096 Jan 26 17:53 root
drwxr-xr-x    1 root     root            40 Jan 26 17:53 run
drwxr-xr-x    2 root     root          4096 Jan 26 17:53 sbin
drwxr-xr-x    2 root     root          4096 Jan 26 17:53 srv
drwxr-xr-x    2 root     root          4096 Jan 26 17:53 sys
drwxrwxrwt    1 root     root            40 Jan 26 17:53 tmp
drwxr-xr-x    7 root     root          4096 Jan 26 17:53 usr
drwxr-xr-x   12 root     root          4096 Jan 26 17:53 var
```

Попробуем его запустить:

```shell
/ $ ./check_flag
Enter flag: sdfdsfsfsd
Wrong flag.
```

Запустить `cat` на этот файл не получится, поэтому придется как-то заставить программу делать то, что нам нужно, уже после запуска. Попытки отладить программу снаружи через `procfs` не получится из-за ограничений безопасности ядра. Придется выкручиваться.

Остается надеяться, что `check_flag` использует динамический линкер. Размер не слишком большой, чтобы включать весь libc, и не слишком маленький, чтобы быть написанным без libc вообще, так что, скорее всего, это правда так.

Полазив по файловой системе или увидев название шелла `ash`, можно понять, что используется Alpine Linux с musl libc, который поддерживает [не так уж и много опций](https://wiki.musl-libc.org/environment-variables). Самой полезной будет `LD_PRELOAD`: с ее помощью можно подгрузить какую-то динамическую библиотеку в процесс, запустив его с переменной окружения. например, `LD_PRELOAD=mymodule.so ./check_flag` подгрузит при старте в процесс `mymodule.so`.

Осталось этот модуль написать. Можно начать с чего-то простого, например,

```c
#include <unistd.h>

__attribute__((constructor)) void init(void) {
	write(1, "Hello, world!\n", 14);
}
```

Соберем эту программу в модуль локально, сожмем и переведем в base64:

```shell
$ gcc mymodule.c -o mymodule.so -shared
$ gzip mymodule.so
$ base64 mymodule.so.gz
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
```

Теперь на сервер этот файл распакуем:

```shell
Enter token: bg00rw2yzql21nvp
/bin/sh: can't access tty; job control turned off
/ $ base64 -d >/tmp/mymodule.so.gz <<EOF
> H4sICA3ryGUAA215bW9kdWxlLnNvAO1bb2wURRSfvfbgCvR6YPmvcBBIQGGpYFU0hWtL20XbgtB+
> UCDLtrdtj9zd1r09So2JGKLREBNI1Bg/GU0MfvFPYqLxiyUoIYTEEvlgYkhQQyyJ0RKjAYxdZ3be
> 2+4Ot4LGGE3ml+z99r15v5nZnbnObu/NM22d7TFFIYgqsoVMW4RkgBsag74HyWz6uYzc5cVWk2hk
> 4mEmKU5MFw/YIncpYQ7qvPbS4Bf4AglzUDeDHpPruT3ZFOZ0jPOaWFgXA11C5XZiS5jHlDAnQF4N
> xwmoT2Sx+6LuDMSJvIqEGe/97stO9u+0txN0KSgQeR0JM7b3GNXNILcPHN5d0F7UOKRiYcbhr4Y6
> 2Jzp6O5l4zLGfFWB8nqwWflvnUt//+Cb785nkheOn7uRfVItT+1kcTieOB+gZ15rzN783GtP3+o6
> 0hX8T9BjXgW/EhG/LsLfTo+VFfy9Xv1Jsngut3H8ia4PFqyiXnIM29F1om/v6dKzpm0O5kqOafd0
> teatotlj9OVNXla5RO8/ZOgDuaKRzz1lklwx55ARO+eYJJ/r61dLlno/6ejc3tKqb1Q3qo3edcXo
> wT/5dSpkP5ke5/KSXA27rQfAxvHFeZeC6yBbwv5xqCCRCfvRvgb1TI8fx5mtnHFsEeMBf1XA/1XA
> H/z7dSngjwf8+IdwJoHJIiEhISEhISEhIfE/xM91y25oR35IaEfjJzcQoj035sTcce3IZ4lTXrnb
> eJa63dXn6Gfd8owXP8QKrnzruu7AMWa7q1+lpQN1y7fx+tzVb/u29lLTO6zel+JvMtp8zZlPm+qG
> pmrcS3XLD7PqTgHT+FEvvtFmtHZKe3FSO/njVu3ktSpNOa2dn3LqaQV3QQUJ9xJvB/Ws/cNNjbSY
> lO/p1Y403WAv7tqLl5052tGmBdQ/sZ12fCJLP07Ha6mt7KPakP7KCC1kJ71U90nS61X8yySr5vSn
> 7OViYgENOLbvVPD++XdMQkJCQkJCQkJCQkJCQuK/B83M56116RHLzmdXzKJvw0urHma/TXq/t066
> rka5gfIw5QzlFyjXXHXdN0BfD6w8tYsoh1LK0jkzE8cU/vvknfQY+8l10ywgmWpPLnqkbvZI4jDZ
> umTz3ZtWrUQ9fX0nH9O4FJkG8++lx/uCn9Xp0MOgffF+A21Lpp6PtdbO2EMb/sfvjoSEhISEhISE
> hISExP8Xft4lYDyQH82wH3iOL+BUC2YG9IvBxrzOpeFwsgT1kN95J5j4jvbLlGt5ekimxFzLMUjS
> xNzORWDPAvsg8GwsB8bczgnI34wJ5fieOhN4IfCaeNg/VB3u5xhwjVDflMv7r0G8Czbex0mw74fy
> 62AHc1D/TWC+uogGId+2o7X1ofSa3r5y0Smn792kblQb1t9X9sxNa8HxZ+3w/Pyrruhn8ylGkmR/
> KuxPgv+Y4F8B/nHB/4DXxmKSyky3x9Dqndf78w1xAOoR5/1BL/4Of/4iXonof9R1veGVzSPjabGk
> cvy7Xn/q/O8R4kOvnkX+OCBOev75N43fWe9zrp+nj7gI9eD9QVzx/Av97wfC9foza/qLC4grlfPT
> VyiV89w3RcQTpXLeektE/F6lcv476bedklMeGFD7yXR6u+4U9H6Wxl4iup619MG81Wfk9axj2SXd
> KB8i/VZhOG86ZpbO2ooRLOk9pxu2bYzqZtGxR8mAbRRMPVsuFEapJGDpLC0+FFoYLVjZct6kfdL1
> 9l3NXW16W/c2loXPamUNlix9yChmWYr9tse7m7u2t1JvR3ev3qaBQNu2i7p6ulpR2tG5o6W5U9/R
> 3r67rUfvaW7pbKNeLyX/z5L7vXT9TDBJv9LOgNvI/g/VQdTSaMEx+ig7NuchPCtajqkOFsvqsG0N
> m7YzGnD1lXP57PpclnjWkFEaImp2tEgr4+zYvOSgaZdyVjFk6LTMNvMGC4Sz4bxDVO8WsFN10IKT
> ktlPVMc8RE3vjqu2lTUcg6jmEIzcUNaetngdfAi5As9pU0YhRyujVfPWeD19pRJR6SQq0AGvNCv/
> Mtg6GdxDELVPByH+T1MV9FH7gxDi3qxmevxK1yLU4/o7KehRJ7b/KOFrr7++VoX5BPjZsqoE9Lhu
> 7iZ8DUQ9rvfIuL4jFMHeQ/hai3pcX5GTQv9jArPctamAHtdv5HRE/xEjULdfX3WYx4T2xet/Fspa
> wMbnD2SMYzELK+iPEmHvi7BvDp/DEOL4Py/o0ymBhXhxe95xQZ9JhVlYRm7Svy7od6bCfCv9W4Ie
> nyeQL0boEe+I/Z8b5lohXrx/74He3wOUDnOdEC/O348EfdR+u6j2Pxf0mXSYXxbixfn7BeHfEXwO
> 9fffwX488X4lBP6a8Gv0n2PxuUQNx0XpvyfhvVj+fkrQ4z7KuKDDfrHnMyWgx31fZzZwTt+i/UlB
> j89DE7epvy7o/X1qDeE4UY9wwYd6fE5LRejF+VOtcJ/4EI761RH6IFfav/Yg6IehkL2v1ZOb//7U
> kMrvMCc2ch4ROiz2f26Efvl9nGtvof8De9IJ97A8AAA=
> EOF
/ $ gunzip /tmp/mymodule.so.gz
/ $ LD_PRELOAD=/tmp/mymodule.so ./check_flag
Hello, world!
Enter flag:
```

Ура, наш код исполнился! Осталось написать какую-нибудь более разумную нагрузку. Для начала стоит вытащить всю память процесса — либо нам повезет и флаг окажется прямо там, либо нам будет что реверсить. Сделать это можно, прочитав `procfs`:

```c
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
```

Нам на удивление везет, и с такой нагрузкой, пайпая вывод в `strings | grep ugra_`, чтобы не искать флаг глазами, мы получаем *его*:

Флаг: **ugra_there_is_light_at_the_end_of_the_tunnel_e696w4sexb5s**
