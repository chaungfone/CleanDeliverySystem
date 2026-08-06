import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const SMS_GATEWAY_URL = Deno.env.get("SMS_GATEWAY_URL")
const SMS_API_KEY = Deno.env.get("SMS_API_KEY")

serve(async (req) => {
  try {
    const { record, old_record, type } = await req.json()

    if (type === "UPDATE" && record.status !== old_record.status) {
      console.log(`Order ${record.id} status changed: ${old_record.status} -> ${record.status}`)

      // Logic to find customer phone number and send SMS
      // In a real scenario, we'd query the DB here if phone isn't in payload

      const message = `Clean Delivery: Your order #${record.id.slice(0,8)} is now ${record.status}.`

      console.log(`Sending notification: "${message}"`)

      // Example HTTP call to SMS Gateway
      /*
      await fetch(SMS_GATEWAY_URL, {
        method: "POST",
        headers: { "Authorization": `Bearer ${SMS_API_KEY}`, "Content-Type": "application/json" },
        body: JSON.stringify({ to: "...", message })
      })
      */
    }

    return new Response(JSON.stringify({ success: true }), {
      headers: { "Content-Type": "application/json" },
      status: 200,
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { "Content-Type": "application/json" },
      status: 400,
    })
  }
})
