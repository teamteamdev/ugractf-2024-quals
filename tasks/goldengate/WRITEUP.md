# Golden Gate: Write-up

Подключаемся по telnet и видим поле для ввода логина. Вводим `ugra`, потом вводим пароль `ucucuga`, попадаем в шелл.

```shell
Welcome to GOLDEN GATE
Enter login: ugra
Enter password: ucucuga
/ $ ls
auth.sh  etc      lib      opt      run      sys      var
bin      flag     media    proc     sbin     tmp
dev      home     mnt      root     srv      usr
/ $ cat flag
cat: can't open 'flag': Permission denied
/ $ cat auth.sh
export ENV=
for c in W e l c o m e " " t o " " G O L D E N " " G A T E; do
	echo -n "$c"
	sleep 0.02
done
echo
trap "echo 'Bye!'; exit" SIGINT
echo -n "Enter login: "
read login
echo -n "Enter password: "
read password
if [[ "$login" != ugra || "$password" != ucucuga ]]; then
	echo "Wrong login and/or password"
	exit 1
fi
exec su "$login"
```

Видим в корне файлы `auth.sh` и `flag`. `flag` нечитаемый для всех, кроме рута, а вот `auth.sh` прочитать можно. В нем устанавливается обработчик сигнала SIGINT, посылаемый нажатием клавиш Ctrl-C, но только после того, как выведется строка `Welcome to GOLDEN GATE`. Попробуем успеть нажать Ctrl-C во время вывода этой строки и получим консоль рута, из которой флаг читается легко:

```shell
/ # cat flag
ugra_thats_how_you_bypassed_autoexec_bat_in_early_days_klgul26t7syy
```

Отметим, что долгое время файл `auth.sh` также был нечитаемым. Намекнуть на то, что Ctrl-C перехватывается, должно было то, что при остановке соединения через Ctrl-C выводится явно нестандартное сообщение Bye.

Есть и альтернативное, гораздо более интересное и найденное случайно участником решение! Если нажать во время вывода `Welcome to GOLDEN GATE` Ctrl-Z, а не Ctrl-C, то активной команде `sleep 0.02` придет сигнал SIGTSTP и она станет фоновой задачей шелла. Это приведет к тому, что команда `exit 1` не завершит интерактивный шелл, а выведет надпись `You have stopped jobs.` и продолжит исполнение, дойдя до команды `su "$login"`. Соответственно, если ввести логин `root`, а пароль ввести неправильный, то ошибка пусть и выведется, но под рутом войти все равно получится:

```shell
Welcome to GOLDEN ^ZGATE[1]+  Stopped                    sleep 0.02

Enter login: root
Enter password:
Wrong login and/or password
You have stopped jobs.
/ #
```

Флаг: **ugra_thats_how_you_bypassed_autoexec_bat_in_early_days_klgul26t7syy**
