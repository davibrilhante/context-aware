ALG=(0 2 4)
COND=(1 2)
SEED=`seq 1 30`
DIST=`seq 10 160`
USERSINF=10
RATEINF=1
USERSSUP=100
RATESUP=0.001
OPTION=2 # full reciprocity in the exhaustive alg and 2 adjacent beams on geolocation alg
TRY=(1 2)

for a in ${ALG[@]}
do
	for c in ${COND[@]}
	do
		for d in ${DIST[@]}
		do
			for s in ${SEED[@]}
			do
				for x  in ${TRY[@]}
				do
					if [ x == 1 ]
					then
						if [ a == 0 ]
						then
							echo -e "python3 newradio.py -a $a -c $c -m 5 -l $d -s $s -r $OPTION -u $USERSINF -t $RATEINF"
						else
							echo -e "python3 newradio.py -a $a -c $c -m 5 -l $d -s $s -d $OPTION -u $USERSINF -t $RATEINF"
						fi
					else
						if [ a == 0 ]
						then
							echo -e "python3 newradio.py -a $a -c $c -m 5 -l $d -s $s -r $OPTION -u $USERSUP -t $RATESUP"
						else
							echo -e "python3 newradio.py -a $a -c $c -m 5 -l $d -s $s -d $OPTION -u $USERSSUP -t $RATESUP"
						fi
					fi
				done
			done
		done
	done
done

