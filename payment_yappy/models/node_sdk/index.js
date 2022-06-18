import { createClient } from 'yappy-node-back-sdk'

const data = JSON.parse(process.argv[2])

const yappyClient = createClient(
    data.merchant_id,
    data.secret_key
);

async function getUrl(environment) {
    if (environment === 'test') {
        const response = await yappyClient.getPaymentUrl(data.payment, false, true); //Pago normal, en modo prueba
        console.log(JSON.stringify(response))
    }
    if (environment === 'enabled') {
        const response = await yappyClient.getPaymentUrl(data.payment); // Pago normal
        console.log(JSON.stringify(response))
    }
}

getUrl(data.environment);

