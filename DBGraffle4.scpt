(*
	Simple connector script for DBGraffle.py
*)
property pyscript : missing value
property default_pyscript : "~/DBGraffle4/DBGraffle4.py"

property graffle : missing value
property default_graffle : "OmniGraffle Professional"

property dbhost : missing value
property default_dbhost : "localhost"

property dbport : missing value
property default_dbport : "5432"

property dbuser : missing value
property default_dbuser : ""

property dbname : missing value
property default_dbname : ""

property schema : missing value
property default_schema : "public"

set update to "NO"

if pyscript is missing value then
	set pyscript to default_pyscript
	set update to "YES"
end if

if graffle is missing value then
	set graffle to default_graffle
	set update to "YES"
end if

if dbhost is missing value then
	set dbhost to default_dbhost
	set update to "YES"
end if

if dbport is missing value then
	set dbport to default_dbport
	set update to "YES"
end if

if dbuser is missing value then
	set dbuser to default_dbuser
	set update to "YES"
end if

if dbname is missing value then
	set dbname to default_dbname
	set update to "YES"
end if

if schema is missing value then
	set schema to default_schema
	set update to "YES"
end if

if update is "NO" then
	display dialog "Update Parameters?" buttons {"Update", "Keep"} default button "Keep"
	set resp to button returned of result
	if resp is not "Keep" then
		set update to "YES"
	end if
end if

if update is "YES" then
	display dialog "Script Location:" default answer pyscript with icon note
	set pyscript to text returned of result
	
	display dialog "OmniGraffle Program:" default answer graffle with icon note
	set graffle to text returned of result
	
	display dialog "Host Name:" default answer dbhost with icon note
	set dbhost to text returned of result
	
	display dialog "Host Port:" default answer dbport with icon note
	set dbport to text returned of result
	
	display dialog "User Name:" default answer dbuser with icon note
	set dbuser to text returned of result
	
	display dialog "Database Name:" default answer dbname with icon note
	set dbname to text returned of result
	
	display dialog "Schema Name:" default answer schema with icon note
	set schema to text returned of result
end if

set cmd to "pythonw " & pyscript
set cmd to cmd & " graffle=\"" & graffle & "\""
set cmd to cmd & " dbhost=\"" & dbhost & "\""
set cmd to cmd & " dbport=\"" & dbport & "\""
set cmd to cmd & " dbuser=\"" & dbuser & "\""
set cmd to cmd & " dbname=\"" & dbname & "\""
set cmd to cmd & " schema=\"" & schema & "\""
do shell script cmd
