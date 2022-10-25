for k in $(seq 0 16)
do
  ./bfc --target "$k|327,327" ./reslock.mdrp
done