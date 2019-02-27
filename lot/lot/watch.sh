while true
    do
        #inotifywait -r -e modify -e move -e create -e delete ../media ~/src/madrona/madrona/media/ | while read line
        inotifywait -r -e modify -e move -e create -e delete ../media | while read line
            do
                python manage.py install_media
            done
    done
