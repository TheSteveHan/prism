if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <new_name>"
    exit
fi
NEW_NAME=$1
find auth -type f|xargs -L 1 -- sed -i'.backup' -e "s/auth/${NEW_NAME}/g"
mv auth $1
find ${NEW_NAME} -name *.backup|xargs -L 1 rm 
