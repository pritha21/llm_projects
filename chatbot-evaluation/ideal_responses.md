# Ideal Response Template for Zwiggy Food Delivery Support

This version matches the phrasing used in `scenarios.yaml`, ensuring consistent evaluation.

## Rubric for Evaluation:
- **Accuracy (30%)**: Correctly references tool or tracker data; factual and relevant.
- **Empathy (30%)**: Acknowledges user frustration and responds with understanding.
- **Resolution (25%)**: Offers an appropriate, policy-aligned action or fix.
- **Clarity & Tone (15%)**: Communicates clearly and politely, without unnecessary wording.

---

## 1. LATE (Late Delivery)
**Scenario**: Order is delayed.
**Ideal Flow**:
- **User**: "my order is late by 50 mins"
- **Agent**: "I am so sorry to hear your order is running this late. My tracker shows it's out for delivery and was expected about 40 minutes ago. Does that match what you're seeing?"
- **User**: "Yes, it's been 50 mins, this is ridiculous."
- **Agent**: "You are right, a delay of this length is unacceptable. To apologize for the long wait, I have just added a credit to your account for your next order. Does this help resolve the issue for you?"

---

## 2. MISS (Missing Item)
**Scenario**: An item is missing.
**Ideal Flow**:
- **User**: "missing Chicken Burger"
- **Agent**: "I'm so sorry to hear an item was missing. My records show your order was for a Chicken Burger, Fries, and a Milkshake. Could you confirm for me that just the Chicken Burger was missing?"
- **User**: "Yes, just the burger."
- **Agent**: "Thank you for confirming. I'm very sorry it was left out. I've just issued a credit for the full value of the Chicken Burger to your account. Has this resolved your issue?"

---

## 3. QUALITY (Food Quality)
**Scenario**: The food was not up to standard.
**Ideal Flow**:
- **User**: "The sushi was warm and stale."
- **Agent**: "That is completely unacceptable, and I am so sorry. I am processing a full refund for the Sushi Platter for you right now. Has this resolved your issue?"
- **User**: "Yes, that works."
- **Agent**: "Thank you for confirming. I’ve completed the refund process and flagged the restaurant for review. Has this resolved your issue fully?"

---

## 4. WRONG (Wrong Order)
**Scenario**: The wrong food was received.
**Ideal Flow**:
- **User**: "I got a pepperoni pizza instead of a veggie one."
- **Agent**: "I've verified that your original order was for a veggie pizza, but you received a pepperoni pizza instead. I can either have the correct veggie pizza sent out to you right away, or I can process a full refund. What would you prefer?"
- **User**: "I'd like a refund."
- **Agent**: "Got it. I’ve gone ahead and processed a full refund for you. It should reflect in your account shortly. Has this resolved your issue?"

---

## 5. PAYMENT (Double Charge)
**Scenario**: Customer was charged twice.
**Ideal Flow**:
- **User**: "I was charged twice for my order."
- **Agent**: "I understand your concern, and I will make this my top priority. My records show your order is being prepared. To escalate this, could you tell me the amount you were charged and how many times you see it? Please don't share any card details."
- **User**: "Charged $20.98 twice today."
- **Agent**: "Thank you. I have immediately escalated this to our billing team. They will review it and contact you by email within 24 hours with a resolution. Has this resolved your issue for now?"

---

## 6. ADDRESS (Wrong Delivery Address)
**Scenario**: The order is going to the wrong address.
**Ideal Flow**:
- **User**: "My order is going to the wrong address!"
- **Agent**: "I see your order is out for delivery and arriving in about 10 minutes. What is the correct address?"
- **User**: "It's 123 Main St."
- **Agent**: "I've just updated the address to 123 Main St and relayed the new instructions to the driver. The ETA in your app will update shortly. Has this resolved your issue?"

---

## 7. COLD (Cold Food)
**Scenario**: Hot food arrived cold.
**Ideal Flow**:
- **User**: "My hot wings arrived cold."
- **Agent**: "I'm so sorry to hear that your hot wings arrived cold. I've checked on the status of your order, and I see that it was delivered. Can you please confirm if everything else in your order was correct, and if the cold temperature was the only issue? I've issued a partial credit to your account for the poor experience. I have also escalated this as a formal service complaint to our delivery team. Has this resolved your issue for now?"
- **User**: "Yes, that's fine."
- **Agent**: "Thank you. I’ve confirmed the credit and complaint have been logged. Has this resolved your issue completely?"

---

## 8. TRACK (Order Tracking)
**Scenario**: Customer wants to know where their order is.
**Ideal Flow**:
- **User**: "Where is my food?"
- **Agent**: "Your order is out for delivery and will arrive in about 5 minutes. Is there anything else I can assist you with?"
- **User**: "Okay, thanks."
- **Agent**: "You’re welcome. I’ll keep an eye on it from here. Enjoy your meal when it arrives!"
