
try:
	import pymysql

	pymysql.install_as_MySQLdb()
except Exception:
	# Optional: allows local dev without PyMySQL installed
	pass
