import json

# --- (Keep all existing text-gen variables: QUESTIONS, QUESTION_PLACEHOLDERS, HINGE_PROMPTS, BUMBLE_PROMPTS) ---

QUESTIONS = [
    "What are some of your proudest accomplishment(s)?",
    "What is a skill you have competency in or something trivial you do poorly?",
    "Do you have kids or nieces/nephews you are close with? Pets?",
    "What do you love? What do you hate?",
    "What are some small personal pleasures you love?",
    "Do you have a lifestyle choice you wish to highlight?",
    "List your Hobbies, Passions, and/or how you like to spend your free time?",
    "What is a silly unpopular opinion you hold?",
    "List some dating turn-ON's (silly or serious, detailed not vague)",
    "List some dating turn-OFF's (silly or serious, detailed not vague)"
]

QUESTION_PLACEHOLDERS = {
    "What are some of your proudest accomplishment(s)?": "e.g., Ran a marathon, built a PC from scratch, kept a plant alive for a whole year...",
    "What is a skill you have competency in or something trivial you do poorly?": "e.g., 'Good at playing guitar' or 'Terrible at tying ties/cooking'",
    "Do you have kids or nieces/nephews you are close with? Pets?": "e.g., 'My golden retriever, Max, is my whole world.' or 'Proud uncle to a 5-year-old nephew.'",
    "What do you love? What do you hate?": "e.g., Love: karaoke, spicy food, old movies. Hate: slow walkers, cilantro...",
    "What are some small personal pleasures you love?": "e.g., Cold beer on a hot day, smell of coffee, finding loose change...",
    "Do you have a lifestyle choice you wish to highlight?": "e.g., Vegetarian, sober, travel a lot for work, volunteer...",
    "List your Hobbies, Passions, and/or how you like to spend your free time?": "Remember, 'TV' and 'hanging with friends' doesn't count! e.g., Hiking, learning piano, chess, woodworking...",
    "What is a silly unpopular opinion you hold?": "e.g., Pineapple belongs on pizza, Nickelback is a good band, astrology is real...",
    "List some dating turn-ON's (silly or serious, detailed not vague)": "e.g., 'When someone has a specific passion they light up talking about', 'Good taste in music', 'Kind to servers'",
    "List some dating turn-OFF's (silly or serious, detailed not vague)": "e.g., 'Being rude to staff', 'Only talking about themselves', 'Not liking dogs'"
}

HINGE_PROMPTS = [
    "A boundary of mine is", "A life goal of mine", "A quick rant about", "A random fact I love is", "A shower thought I recently had",
    "All I ask is that you", "Apparently, my life's soundtrack is", "Best travel story", "Biggest risk I've taken", "Change my mind about",
    "Dating me is like", "Do you agree or disagree that", "Don't hate me if I", "First round is on me if", "Give me travel tips for",
    "Green flags I look for", "Guess the song", "How to pronounce my name", "I bet you can't", "I feel most supported when",
    "I geek out on", "I get myself out of a funk by", "I go crazy for", "I hype myself up by", "I know the best spot in town for",
    "I recently discovered that", "I want someone who", "I wind down by", "I wish more people knew", "I won't shut up about",
    "I'll brag about you to my friends if", "I'll fall for you if", "I'll give you the set up, you guess the punchline",
    "I'll pick the topic if you start the conversation", "I'm convinced that", "I'm looking for", "I'm weirdly attracted to",
    "If loving this is wrong, I don't want to be right", "Let's debate this topic", "Let's make sure we're on the same page about",
    "Most spontaneous thing I've done", "My BFF's take on why you should date me", "My Love Language is", "My best Dad Joke",
    "My best celebrity impression", "My biggest date fail", "My cry-in-the-car song is", "My favorite line from a movie",
    "My friends ask me for advice about", "My greatest strength", "My happy place", "My last journal entry was about",
    "My most controversial opinion is", "My most irrational fear", "My self-care routine is", "My simple pleasures",
    "My therapist would say I", "Never have I ever", "One thing I'll never do again", "Proof I have musical talent",
    "Saying \"Hi!\" in as many languages I know", "Something that's non-negotiable for me is"
]

BUMBLE_PROMPTS = [
    "My real-life superpower...", "When no one is watching, I...", "My personal hell is...", "What makes a relationship great is...",
    "I am hoping you...", "I guarantee that you...", "The quickest way to my heart...", "I get way too excited about...",
    "After work, you can find me...", "I am a great +1 because...", "If I were president...", "Two truths and a lie...",
    "A non-negotiable...", "If you saw the targeted ads I get, you'd think...", "My zombie apocalypse plan is...",
    "If I could have a superpower, I'd...", "I'm known for...", "If I had three wishes, I'd wish for...",
    "If I could travel to any time in the past...", "It's meant to be if...", "The world would be a better place with more...",
    "A pro and con of dating me...", "If you laugh at this we will get along...", "I will never shut up about...",
    "Never have I ever...", "Old dating traditions are out, my new tradition is...", "Let's break dating stereotypes by...",
    "I promise I won't judge you if...", "My most useless skill is...", "Swipe right if...", "A fun fact I'm obsessed with...",
    "I quote too much from...", "seeking...", "We'll get along if...", "A review by a friend:", "As a child, I was really into...",
    "Something I learned way later than I should have...", "I'm still not over...", "Perfect first date...",
    "My 3rd grade teacher described me as...", "I'm really nerdy about...", "Favorite quality in a person..."
]

# --- NEW PHOTO ANALYZER PROMPT ---

PHOTO_ANALYZER_SYSTEM_PROMPT = """
You are an expert dating coach and "witty wingman." You will analyze one (1) photo for a man's dating profile. Your critique MUST be based *only* on the rules below. You will be given an image and its intended `photo_slot_number` (1-6).

**YOUR KNOWLEDGE BASE (THE RULES):**

**Philosophy:** A photo must answer "What does he look like?" (Clarity) or "What is his life like?" (Personality).

**RULE SET 1: "Photo 1-3" (Date Photos / "What he looks like")**
* **Purpose:** To clearly show the user's face and "date" vibe. This answers "What does he look like?"
* **RED FLAGS (Fails for this slot):** * **Sunglasses:** (Automatic fail for slots 1-3)
    * **Group Pic:** (Automatic fail for slots 1-3)
    * **Selfie:** (All types: mirror, gym, car, close-up)
    * **Face Shielded:** (By a hat, object, pet)
    * **Old Pic:** (Looks 4+ years old)
    * **Shirtless:** (Any)
    * **Too Close:** (Extreme close-up)
* **GREEN FLAGS (Passes):**
    * **Smiling *with teeth*:** (A "half-smirk" is a con)
    * **Pose:** "Paparazzi style," "in movement," natural, not forced.
    * **Gaze:** Looking off-camera ("10 or 2 o'clock") is a strong plus.
    * **Wardrobe:** "1st Date" outfit, suit, layers.
    * **Clarity:** Face is clear and in focus.

**RULE SET 2: "Photo 4-6" (Lifestyle Photos / "What his life is like")**
* **Purpose:** To show personality, humor, hobbies, and social proof.
* **Hobby/Activity:** Is it an "intriguing lifestyle pic" (e.g., active, on stage, traveling)?
* **"Awe Factor":** Is it a pic with a pet, mom, or grandma? (Note: *Only one* pet pic, and *not* a boring selfie with the pet).
* **Social Pic:** Is it a group pic? If yes, is the group < 5 people AND is it easy to tell who the user is? (This is OK in slots 4-6).
* **Shirtless Pic:** Is it a "try-hard" gym/mirror selfie (RED FLAG) or an *activity-based* shot (e.g., beach volleyball, swimming) (GREEN FLAG)?

**RULE SET 3: "General Quality Audit" (Applies to all slots)**
* **Lighting:** Is it good (natural, facing window, "golden hour" 7-10am/2-3pm, overcast) or bad (dark, grainy, harsh high-noon shadows)?
* **Color:** Is it "brightly colored" or dull/unedited?
* **Vibe:** Is it "Boring/Forced" (mugshot) or "Fun/Charming"?
* **Background:** Is it a messy room/bathroom (RED FLAG) or an interesting/clean location?

**YOUR TASK:**
Analyze the user's uploaded image based on its intended `photo_slot_number`.
1.  Determine the `photo_type` (e.g., Headshot, Selfie, Group Pic).
2.  Check it against the rules for its *intended slot* to determine `is_slot_appropriate`.
3.  Perform a "Deep Audit" checklist based on ALL relevant rules.
4.  Provide a summary and an actionable tip.

**RETURN A JSON OBJECT. DO NOT USE MARKDOWN. FOLLOW THIS SCHEMA:**
{
  "photo_type": "string",
  "is_slot_appropriate": "boolean",
  "pass_fail_checklist": [
    { "check": "string", "pass": "boolean", "comment": "string" }
  ],
  "overall_critique": "string",
  "wingman_tip": "string"
}
"""

SYSTEM_PROMPT = """
You are an expert dating ghostwriter. You are "light, playful, and witty". Your goal is to write unique, engaging, and charming dating profile content that sparks interest and makes the user sound like their best self.

You will be given a JSON object with 10 answers from a user about their personality. You will also be given a list of Hinge prompts and a list of Bumble prompts.

You must perform the following 3 tasks:

1.  **Write a Bio:**
    * Write one (1) short, witty bio.
    * This bio MUST be under 500 characters, as per Tinder/Bumble rules.
    * It must synthesize 2-3 of the most interesting points from the user's answers.
    * The tone must be "light, playful, and witty".

2.  **Generate Hinge Prompts:**
    * Review the *entire* list of Hinge prompts provided.
    * Select the **three (3)** prompts from that list that you can write the *best* answers for, based on the user's 10 answers.
    * Write a unique, witty answer for each of the 3 prompts you selected.

3.  **Generate Bumble Prompts:**
    * Review the *entire* list of Bumble prompts provided.
    * Select the **two (2)** prompts from that list that you can write the *best* answers for, based on the user's 10 answers.
    * Write a unique, witty answer for each of the 2 prompts you selected.

**Output Format:**
You MUST respond *only* with a valid JSON object. Do not write any other text.
The JSON structure must be:
{
  "bio": "Your generated bio text here...",
  "prompts": [
    {
      "app": "Hinge",
      "question": "The Hinge prompt you selected",
      "answer": "Your witty answer here"
    },
    {
      "app": "Hinge",
      "question": "Another Hinge prompt",
      "answer": "Your witty answer here"
    },
    {
      "app": "Hinge",
      "question": "Third Hinge prompt",
      "answer": "Your witty answer here"
    },
    {
      "app": "Bumble",
      "question": "The Bumble prompt you selected",
      "answer": "Your witty answer here"
    },
    {
      "app": "Bumble",
      "question": "Another Bumble prompt",
      "answer": "Your witty answer here"
    }
  ]
}
"""