use 

python radius.py yourfile.csv 

but specify whatever your file is.
it will output the non duplicates to a list and file.  you can specify

--output outputfile.csv 

uses default radius as 0.0001degrees (11meters) and can be changed with

--radius 0.0001 

full command

python radius.py in.csv --radius 0.01 --output out.csv 
