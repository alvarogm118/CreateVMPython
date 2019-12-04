import sys
import os
from subprocess import call
import configparser #Unicamente para python3
config = configparser.ConfigParser()
import xml.etree.ElementTree as etree
mv = ["c1", "lb"] #Array inicial que siempre tiene c1 y lb y que luego se le incorporan los servidores

# CREAR
if str(sys.argv[1]) == "crear" :
    # Comprobacion de que si hay 2o parametro que sea valido (Se comprueba si es un entero y si este estaria en el rango de 1 a 5)
    # Con la comprobacion 'if int(sys.argv[2]) < 1 or int(sys.argv[2]) > 5 :' solo se comprobaria si el entero estuviera en el rango, NO SI ES UN STRING (por ejemplo si se escribiera 'a' esa comprobacion seria inutil)
    if len(sys.argv) > 2 :
        if str(sys.argv[2]) != "1" and str(sys.argv[2]) != "2" and str(sys.argv[2]) != "3" and str(sys.argv[2]) != "4" and str(sys.argv[2]) != "5" :
            print('El parametro opcional no es un entero o no esta en el rango entre 1 y 5')
            sys.exit()
    # Creacion directorios y copias de imagen y plantilla
    os.system("mkdir /mnt/tmp/pf1")
    os.system("cp cdps-vm-base-pf1.qcow2 /mnt/tmp/pf1/.")
    os.system("cp plantilla-vm-pf1.xml /mnt/tmp/pf1/plantilla-vm-pf1.xml")

    #Creacion y modificacion fichero .cfg
    config['DEFAULT'] = {'num_serv' : '2'}
    config['CUSTOM'] = {'num_serv' : 'x'}
    with open('/mnt/tmp/pf1/pf1.cfg', 'w') as f:
        config.write(f)

    config.read("/mnt/tmp/pf1/pf1.cfg")

    if len(sys.argv) > 2 : # Aqui ya operamos con este segundo parametro
        config.set("CUSTOM", "num_serv", sys.argv[2])
        with open("/mnt/tmp/pf1/pf1.cfg", 'w') as f:
            config.write(f)
        num_serv = config.getint("CUSTOM", "num_serv")
    else :
        num_serv = config.getint("DEFAULT", "num_serv")

    for i in range(num_serv) :
        mv.append("s"+str(i+1)) #Actualizacion array

    # Creacion MVs
    for item in mv :
        os.system("qemu-img create -f qcow2 -b /mnt/tmp/pf1/cdps-vm-base-pf1.qcow2 /mnt/tmp/pf1/"+item+".qcow2")
        os.system("cp /mnt/tmp/pf1/plantilla-vm-pf1.xml /mnt/tmp/pf1/"+item+".xml")
        # Cargamos el fichero xml
        tree = etree.parse('/mnt/tmp/pf1/'+ item +'.xml')
        # Buscamos la etiqueta 'nombre' imprimimos su valor y luego lo cambiamos
        root = tree.getroot()
        name = root.find("name")
        print(name.text)
        name.text = item
        print(name.text)
        # Buscamos el nodo source dentro de disk bajo devices y cambiamos el atributo de file
        source=root.find("./devices/disk/source[@file='/mnt/tmp/XXX/XXX.qcow2']")
        print(source.get("file"))
        source.set("file", '/mnt/tmp/pf1/'+ item +'.qcow2')
        print(source.get("file"))
        # Buscamos el nodo source dentro de interface bajo devices y cambiamos el atributo de bridge
        source=root.find("./devices/interface/source[@bridge='XXX']")
        print(source.get("bridge"))
        if item == "c1" or item == "lb" :
            source.set("bridge", "LAN1")
            print(source.get("bridge"))
        else :
            source.set("bridge", "LAN2")
            print(source.get("bridge"))

        tree_w = etree.ElementTree(root)
        tree_w.write('/mnt/tmp/pf1/'+ item +'.xml')

    # Caso especial de lb con LAN1 y LAN2
    os.system("mv /mnt/tmp/pf1/lb.xml /mnt/tmp/pf1/lb-00.xml -f")
    lbin = open('/mnt/tmp/pf1/lb-00.xml', 'r')
    lbout = open('/mnt/tmp/pf1/lb.xml', 'w')
    for line in lbin:
        if "</interface>" in line :
            lbout.write(line)
            lbout.write('    <interface type="bridge">\n')
            lbout.write('      <source bridge="LAN2" />\n')
            lbout.write('      <model type="virtio" />\n')
            lbout.write('    </interface>\n')
        else :
            lbout.write(line)
    lbin.close()
    lbout.close()
    print("LAN2")
    os.system("rm /mnt/tmp/pf1/lb-00.xml -f")

    # Creacion de LANs
    os.system("sudo brctl addbr LAN1") #Para borrar es sudo brctl delbr LANx
    os.system("sudo brctl addbr LAN2")
    os.system("sudo ifconfig LAN1 up") #Para pararlo es sudo ifconfig LANx down
    os.system("sudo ifconfig LAN2 up")

    # Configuracion interfaces host
    os.system("sudo ifconfig LAN1 10.0.1.3/24")
    os.system("sudo ip route add 10.0.0.0/16 via 10.0.1.1")

    # Configuracion MVs
    for item in mv :
        os.system("sudo virsh define /mnt/tmp/pf1/"+ item +".xml")

        os.system("mkdir /mnt/tmp/pf1/"+ item)

        os.system("sudo virt-edit -a /mnt/tmp/pf1/"+ item +".qcow2 /etc/hostname -e 's/cdps/"+ item +"/'") #hostname
        print(item)

        os.system("sudo virt-edit -a /mnt/tmp/pf1/"+ item +".qcow2 /etc/hosts -e 's/127.0.1.1 cdps cdps/127.0.1.1 "+ item +"/'") #hosts
        print("127.0.1.1 "+ item)

        os.system("sudo virt-copy-out -a /mnt/tmp/pf1/"+ item +".qcow2 /etc/network/interfaces /mnt/tmp/pf1/"+ item +"/.") #interfaces
        os.system("mv /mnt/tmp/pf1/"+ item +"/interfaces /mnt/tmp/pf1/"+ item +"/interfaces-00")
        if item == "c1" :
            min = open('/mnt/tmp/pf1/'+ item +'/interfaces-00', 'r')
            mout = open('/mnt/tmp/pf1/'+ item +'/interfaces', 'w')
            for line in min:
                if "iface eth0 inet dhcp" in line :
                    mout.write('iface eth0 inet static \n')
                    mout.write("address 10.0.1.2 \n")
                    mout.write("netmask 255.255.255.0 \n")
                    mout.write("gateway 10.0.1.1 \n")
                else :
                    mout.write(line)
            min.close()
            mout.close()
            os.system("sudo virt-copy-in -a /mnt/tmp/pf1/"+ item +".qcow2 /mnt/tmp/pf1/"+ item +"/interfaces /etc/network")
            os.system("sudo virt-cat -a /mnt/tmp/pf1/"+ item +".qcow2 /etc/network/interfaces")
        elif item == "lb" :
            min = open('/mnt/tmp/pf1/'+ item +'/interfaces-00', 'r')
            mout = open('/mnt/tmp/pf1/'+ item +'/interfaces', 'w')
            for line in min:
                if "iface eth0 inet dhcp" in line :
                    mout.write('iface eth0 inet static \n')
                    mout.write("address 10.0.1.1 \n")
                    mout.write("netmask 255.255.255.0 \n")
                    mout.write("\n")
                    mout.write('auto eth1 \n')
                    mout.write('iface eth1 inet static \n')
                    mout.write("address 10.0.2.1 \n")
                    mout.write("netmask 255.255.255.0 \n")
                else :
                    mout.write(line)
            min.close()
            mout.close()
            os.system("sudo virt-edit -a /mnt/tmp/pf1/lb.qcow2 /etc/sysctl.conf -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'")
            print("net.ipv4.ip_forward=1")
            os.system("sudo virt-copy-in -a /mnt/tmp/pf1/"+ item +".qcow2 /mnt/tmp/pf1/"+ item +"/interfaces /etc/network")
            os.system("sudo virt-cat -a /mnt/tmp/pf1/"+ item +".qcow2 /etc/network/interfaces")
        else : #Para los servidores que haya
            sin = open('/mnt/tmp/pf1/'+ item +'/interfaces-00', 'r')
            sout = open('/mnt/tmp/pf1/'+ item +'/interfaces', 'w')
            for line in sin:
                if "iface eth0 inet dhcp" in line :
                    sout.write('iface eth0 inet static \n')
                    sout.write("address 10.0.2.1"+ str(mv.index(item)-1) +" \n")
                    sout.write("netmask 255.255.255.0 \n")
                    sout.write("gateway 10.0.2.1 \n")
                else :
                    sout.write(line)
            sin.close()
            sout.close()
            os.system("sudo virt-copy-in -a /mnt/tmp/pf1/"+ item +".qcow2 /mnt/tmp/pf1/"+ item +"/interfaces /etc/network")
            os.system("sudo virt-cat -a /mnt/tmp/pf1/"+ item +".qcow2 /etc/network/interfaces")

            s = open('/mnt/tmp/pf1/'+ item +'/index.html', 'w') #index.html
            s.write(item +'\n')
            s.close()
            os.system("sudo virt-copy-in -a /mnt/tmp/pf1/"+ item +".qcow2 /mnt/tmp/pf1/"+ item +"/index.html /var/www/html")
            os.system("sudo virt-cat -a /mnt/tmp/pf1/"+ item +".qcow2 /var/www/html/index.html")

#ARRANCAR
if str(sys.argv[1]) == "arrancar" :
    #Carga del valor num_serv y aumento del array mv
    config.read("/mnt/tmp/pf1/pf1.cfg")
    custom = config.get("CUSTOM", "num_serv")
    if custom == 'x' :
        num_serv = config.getint("DEFAULT", "num_serv")
    else :
        num_serv = config.getint("CUSTOM", "num_serv")
    for i in range(num_serv) :
        mv.append("s"+str(i+1))

    if len(sys.argv) > 2 :
        for item in mv :
            if str(sys.argv[2]) == item :
                os.system("sudo virsh start "+ item)
                os.system("xterm -e 'sudo virsh console "+ item +"' &")
    else :
        for item in mv :
            os.system("sudo virsh start "+ item)
            os.system("xterm -e 'sudo virsh console "+ item +"' &")

#PARAR
if str(sys.argv[1]) == "parar" :
    #Carga del valor num_serv y aumento del array mv
    config.read("/mnt/tmp/pf1/pf1.cfg")
    custom = config.get("CUSTOM", "num_serv")
    if custom == 'x' :
        num_serv = config.getint("DEFAULT", "num_serv")
    else :
        num_serv = config.getint("CUSTOM", "num_serv")
    for i in range(num_serv) :
        mv.append("s"+str(i+1))

    if len(sys.argv) > 2 :
        for item in mv :
            if str(sys.argv[2]) == item :
                os.system("sudo virsh shutdown "+ item)
    else :
        for item in mv :
            os.system("sudo virsh shutdown "+ item)

# MONITOR
if str(sys.argv[1]) == "monitor" :
    os.system("watch 'python3 pf1.py m'")

if str(sys.argv[1]) == "m" : #Con este no se haría watch, así que poner siempre monitor
    os.system("sudo virsh list")
    #Carga del valor num_serv y aumento del array mv
    config.read("/mnt/tmp/pf1/pf1.cfg")
    custom = config.get("CUSTOM", "num_serv")
    if custom == 'x' :
        num_serv = config.getint("DEFAULT", "num_serv")
    else :
        num_serv = config.getint("CUSTOM", "num_serv")
    for i in range(num_serv) :
        mv.append("s"+str(i+1))
    for item in mv :
        os.system("sudo virsh domstate "+ item)
        os.system("sudo virsh dominfo "+ item)
        os.system("sudo virsh cpu-stats "+ item)

'''
# MONITOR
# gnome-terminal -- bash -c "watch 'python3 pf1.py monitor'; exec bash"
if str(sys.argv[1]) == "monitor" :
    os.system("sudo virsh list")
    #Carga del valor num_serv y aumento del array mv
    config.read("/mnt/tmp/pf1/pf1.cfg")
    custom = config.get("CUSTOM", "num_serv")
    if custom == 'x' :
        num_serv = config.getint("DEFAULT", "num_serv")
    else :
        num_serv = config.getint("CUSTOM", "num_serv")
    for i in range(num_serv) :
        mv.append("s"+str(i+1))
    for item in mv :
        #os.system("sudo virsh domstate "+ item)
        os.system("sudo virsh dominfo "+ item)
        #os.system("sudo virsh cpu-stats "+ item)
'''

#DESTRUIR
if str(sys.argv[1]) == "destruir" :
    #Carga del valor num_serv y aumento del array mv
    config.read("/mnt/tmp/pf1/pf1.cfg")
    custom = config.get("CUSTOM", "num_serv")
    if custom == 'x' :
        num_serv = config.getint("DEFAULT", "num_serv")
    else :
        num_serv = config.getint("CUSTOM", "num_serv")
    for i in range(num_serv) :
        mv.append("s"+str(i+1))

    for item in mv :
        os.system("sudo virsh destroy "+ item)
        os.system("sudo virsh undefine "+ item)

        os.system("rm /mnt/tmp/pf1/"+ item +"/interfaces -f")
        os.system("rm /mnt/tmp/pf1/"+ item +"/interfaces-00 -f")
        if item != "c1" and item != "lb" :
            os.system("rm /mnt/tmp/pf1/"+ item +"/index.html -f")
        os.system("rmdir /mnt/tmp/pf1/"+ item)

    os.system("sudo ifconfig LAN1 down")
    os.system("sudo ifconfig LAN2 down")
    os.system("sudo brctl delbr LAN1")
    os.system("sudo brctl delbr LAN2")

    os.system("rm /mnt/tmp/pf1/*.qcow2 -f")
    os.system("rm /mnt/tmp/pf1/*.xml -f")
    os.system("rm /mnt/tmp/pf1/pf1.cfg -f")

    os.system("rmdir /mnt/tmp/pf1")
