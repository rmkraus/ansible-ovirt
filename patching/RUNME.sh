source ../secrets.sh
INVENTORY="../hosts/cluster"


./patch_manager.yml -i "$INVENTORY" $@ || exit 1
./patch_hosts.yml   -i "$INVENTORY" $@ || exit 1
