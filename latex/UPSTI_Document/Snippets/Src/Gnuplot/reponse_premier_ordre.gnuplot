set table "Src/Gnuplot/reponse_premier_ordre.table"; set format "%.5f"
set samples 50.0; plot [x=0:6] 0.318*(1-exp(-1*x))
