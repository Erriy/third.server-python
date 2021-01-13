let mdns = require('multicast-dns')();

let port = process.env.PORT ? process.env.PORT : 80;
let IPAdress = '';
const interfaces = require('os').networkInterfaces();
for(let devName in interfaces){
    let iface = interfaces[devName];
    for(let i=0;i<iface.length;i++){
        let alias = iface[i];
        if(alias.family === 'IPv4' && alias.address !== '127.0.0.1' && !alias.internal){
            IPAdress = alias.address;
        }
    }
}


mdns.on('query', function(query) {
    let cond = query.questions.filter(x=>('third' === x.name.toLowerCase() && 'SRV' == x.type.toUpperCase()));
    if(cond.length > 0) {
        console.log(cond)
        mdns.respond({
            answers: [{
                name: 'third',
                type: 'SRV',
                data: {
                    port: port,
                    target: IPAdress
                }
            }]
        });
    }
});

