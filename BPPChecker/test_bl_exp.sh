for k in $(seq 0 2)
do
  echo "-----result of bl_$k-----"
  python3 run.py -b 5 ./benchmarks/"bl_$k"
  python3 run.py -b 10 ./benchmarks/"bl_$k" 
  python3 run.py -b 20 ./benchmarks/"bl_$k"
  python3 run.py -b 50 ./benchmarks/"bl_$k"
done