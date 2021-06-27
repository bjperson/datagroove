#!/bin/bash

rm -rf ./resources/*

wget -q "https://www.data.gouv.fr/fr/datasets/r/970aafa0-3778-4d8b-b9d1-de937525e379" -O ./resources/reuse.csv
wget -q "https://www.data.gouv.fr/fr/datasets/r/b7bbfedc-2448-4135-a6c7-104548d396e7" -O ./resources/organization.csv
wget -q "https://www.data.gouv.fr/fr/datasets/r/4babf5f2-6a9c-45b5-9144-ca5eae6a7a6d" -O ./resources/resource.csv
wget -q "https://www.data.gouv.fr/fr/datasets/r/f868cca6-8da1-4369-a78d-47463f19a9a3" -O ./resources/dataset.csv

rm -f ./bin/datagroove.db

sqlite3 -separator ';' ./bin/datagroove.db ".import ./resources/reuse.csv reuse"
sqlite3 -separator ';' ./bin/datagroove.db ".import ./resources/organization.csv organization"
sqlite3 -separator ';' ./bin/datagroove.db ".import ./resources/resource.csv resource"
sqlite3 -separator ';' ./bin/datagroove.db ".import ./resources/dataset.csv dataset"

sqlite3 ./bin/datagroove.db ".read ./bin/commands.txt"

python3 ./bin/groove.py

wget -q "https://bjperson.github.io/ign-bookmarklet/resources/atom.xml" -O ./flux/ign.xml
