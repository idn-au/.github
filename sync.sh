REPOS=$(gh repo list idn-au --no-archived --limit 100 --json name --jq '.[].name')
for repo in $REPOS; do
    if [ $repo != ".github" ]; then
        echo "Labels in $repo:"
        labels=$(gh label list --repo idn-au/$repo --json name --jq '.[].name')
        if [ "${labels[@]}" != "" ]; then
            echo "${labels[@]}"
            echo "Deleting current labels..."
            echo "${labels[@]}" | while read -r label; do
                gh label delete "$label" --repo idn-au/$repo --yes
            done
            echo "Current labels deleted"
        fi
        echo "Cloning new labels..."
        gh label clone idn-au/.github --repo idn-au/$repo
        echo "New labels cloned"
    fi
done
