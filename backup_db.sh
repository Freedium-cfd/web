sudo docker exec -t postgres_freedium pg_dumpall -c -U postgres | brotli --best > dump_`date +%Y-%m-%d"_"%H_%M_%S`.sql.br
