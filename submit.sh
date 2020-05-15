#!/bin/bash

touch running
ALG=(0 2 4)
COND=(1 2)
SEED=`seq 1 30`
DIST=`seq 10 4 170`
USERSINF=10
RATEINF=1
USERSSUP=100
RATESUP=0.01
OPTION=2 # full reciprocity in the exhaustive alg and 2 adjacent beams on geolocation alg
TRY=(1 2)

for a in ${ALG[@]}
do
	for c in ${COND[@]}
	do
		for d in ${DIST[@]}
		do
			for x  in ${TRY[@]}
			do
				for s in ${SEED[@]}
				do
					if [ $x == 1 ]; then
						if [ $a == 0 ]; then
							echo -e "python3 newradio.py -a $a -c $c -m 5 -l $d -s $s -r $OPTION -u $USERSINF -t $RATEINF >> out2/$a-$c-$d-$s-$USERSINF-$RATEINF" >> running
						else
							echo -e "python3 newradio.py -a $a -c $c -m 5 -l $d -s $s -d $OPTION -u $USERSINF -t $RATEINF >> out2/$a-$c-$d-$s-$USERSINF-$RATEINF" >> running
						fi
					else
						if [ $a == 0 ]; then
							echo -e "python3 newradio.py -a $a -c $c -m 5 -l $d -s $s -r $OPTION -u $USERSSUP -t $RATESUP >> out2/$a-$c-$d-$s-$USERSSUP-$RATESUP" >> running
						else
							echo -e "python3 newradio.py -a $a -c $c -m 5 -l $d -s $s -d $OPTION -u $USERSSUP -t $RATESUP >> out2/$a-$c-$d-$s-$USERSSUP-$RATESUP" >> running
						fi
					fi
				done
			done
		done
	done
done

