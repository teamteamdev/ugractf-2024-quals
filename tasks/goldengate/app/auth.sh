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
