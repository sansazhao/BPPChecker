for k in $(seq 0 5)
do
  ./bfc --target "$k|68,68" ./pipe.mdrp
done