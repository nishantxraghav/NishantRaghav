/**
 * Ported from Lume: src/lib/distortionDetector.js (github.com/nishantxraghav/Lume).
 * Same patterns and weights as the app. Regenerate rather than hand-edit.
 */
export type Trigger = { pattern: RegExp; weight: number };
export type Distortion = { id: string; name: string; reframe: string; triggers: Trigger[] };

export const DISTORTIONS: Distortion[] = [
  {
    id: "allOrNothing",
    name: "All-or-nothing thinking",
    reframe: "Is it really always, or just this time? Can you think of even one exception?",
    triggers: [
      { pattern: /\b(always|never|every\s*time|not\s*once|without\s*exception)\b/i, weight: 2 },
      { pattern: /\b(complete(ly)?|total(ly)?|absolute(ly)?|utter(ly)?)\s+(fail|useless|wrong|stupid|hopeless|disaster)/i, weight: 3 },
      { pattern: /\b(everyone|no\s*one|nobody|everybody)\s+(hates?|ignores?|leaves?|knows?)/i, weight: 2 },
      { pattern: /\b(either|nothing)\b.{0,30}\b(or|works?|matters?)\b/i, weight: 1 },
      { pattern: /i('m|\s+am)\s+(always|never)\s+the\s+one/i, weight: 2 },
      { pattern: /\b(ruined|destroyed|completely\s+broken|total\s+failure|utter\s+disaster)\b/i, weight: 2 },
      { pattern: /\bnot\s+a\s+single\b/i, weight: 1 },
      { pattern: /\b(all|none|every|no)\s+(my|their|his|her)\s+(fault|problem|doing|choice)/i, weight: 2 },
    ],
  },
  {
    id: "overgeneralisation",
    name: "Overgeneralisation",
    reframe: "Is this really a permanent pattern, or might this be one difficult moment?",
    triggers: [
      { pattern: /\b(this\s+always\s+happens|it('s|\s+is)\s+always\s+like\s+this|same\s+thing\s+every\s+time)\b/i, weight: 3 },
      { pattern: /\bnothing\s+(ever\s+)?(works|changes|gets\s+better|helps)\b/i, weight: 3 },
      { pattern: /\bthis\s+is\s+just\s+how\s+(i\s+am|things\s+are|it\s+always\s+is|life\s+is)\b/i, weight: 2 },
      { pattern: /\bi('m|\s+am)\s+(always|constantly|forever)\s+(making|doing|being)\b/i, weight: 2 },
      { pattern: /\beveryone\s+(always|always\s+ends\s+up|eventually)\b/i, weight: 2 },
      { pattern: /\b(pattern|story\s+of\s+my\s+life|never\s+changes|keeps\s+happening)\b/i, weight: 2 },
      { pattern: /\bno\s+matter\s+what\s+i\s+do\b/i, weight: 2 },
    ],
  },
  {
    id: "mentalFilter",
    name: "Mental filter",
    reframe: "What else happened in that situation that you might not be giving weight to?",
    triggers: [
      { pattern: /\b(only|just)\s+(one|the)\s+(bad|negative|wrong|worst|terrible|awful)\b/i, weight: 2 },
      { pattern: /\bcan'?t\s+(stop\s+)?(thinking|focusing|dwelling)\s+(about|on)\b/i, weight: 2 },
      { pattern: /\b(ruins?|spoils?|overshadows?)\s+(everything|it\s+all|the\s+whole|my\s+(whole|entire))\b/i, weight: 3 },
      { pattern: /\beven\s+(though|if).{0,40}(still|only\s+see|focus\s+on\s+the\s+bad)\b/i, weight: 2 },
      { pattern: /\bignoring\s+the\s+(good|positive|rest)\b/i, weight: 2 },
      { pattern: /\b(fixated?|obsessed?|stuck)\s+on\b/i, weight: 1 },
      { pattern: /\ball\s+i\s+can\s+(see|think\s+about|notice)\s+is\b/i, weight: 3 },
    ],
  },
  {
    id: "disqualifyPositive",
    name: "Disqualifying the positive",
    reframe: "What if that compliment or achievement was genuine: what would that mean for you?",
    triggers: [
      { pattern: /\b(but\s+)?(that\s+doesn'?t\s+(count|matter)|it\s+doesn'?t\s+mean\s+anything)\b/i, weight: 3 },
      { pattern: /\b(it\s+was\s+)?(just\s+)?(luck|accident|fluke|coincidence|one\s+time\s+thing)\b/i, weight: 2 },
      { pattern: /\banyone\s+(could('ve|\s+have)|can|would)\s+have\s+done\s+(that|it|the\s+same)\b/i, weight: 2 },
      { pattern: /\bthey'?re?\s+(just|only)\s+(being\s+)?(nice|polite|saying\s+that)\b/i, weight: 2 },
      { pattern: /\b(don'?t|can'?t)\s+(take|accept)\s+a\s+compliment\b/i, weight: 2 },
      { pattern: /\bit\s+(wasn'?t|isn'?t)\s+really\s+(that\s+)?(good|great|impressive|much)\b/i, weight: 2 },
    ],
  },
  {
    id: "mindReading",
    name: "Mind reading",
    reframe: "What actual evidence do you have for what they're thinking? Is there another explanation?",
    triggers: [
      { pattern: /\b(i\s+know|i\s+can\s+tell|i'?m\s+sure|obviously)\s+(they|he|she|everyone)\s+(think|hate|dislike|is\s+annoyed|doesn'?t\s+like|is\s+judging|is\s+disappointed)\b/i, weight: 3 },
      { pattern: /\bthey('re|\s+are)\s+(definitely|probably|clearly)\s+(mad|upset|annoyed|angry|disappointed)\s+at\s+me\b/i, weight: 3 },
      { pattern: /\b(must\s+think|must\s+hate|must\s+find)\s+(me|i'?m|i\s+am)\b/i, weight: 2 },
      { pattern: /\bhe\s+didn'?t\s+(reply|text|call).{0,40}(must\s+(mean|be)|probably|obviously)\b/i, weight: 2 },
      { pattern: /\b(i\s+know\s+exactly|i\s+can\s+tell\s+by)\b/i, weight: 2 },
      { pattern: /\b(they|everyone)\s+(are|is)\s+(judging|laughing|talking\s+about|making\s+fun\s+of)\s+me\b/i, weight: 3 },
      { pattern: /\bshe\s+hates?\s+me\b/i, weight: 3 },
    ],
  },
  {
    id: "fortuneTelling",
    name: "Fortune telling",
    reframe: "You're predicting the future: but how accurate have negative predictions like this been in the past?",
    triggers: [
      { pattern: /\b(it('s|\s+is)\s+going\s+to|this\s+will)\s+(fail|go\s+wrong|be\s+a\s+disaster|not\s+work|end\s+badly)\b/i, weight: 3 },
      { pattern: /\bi('m|\s+am)\s+going\s+to\s+(fail|mess\s+up|embarrass|ruin|lose)\b/i, weight: 3 },
      { pattern: /\b(i\s+know|i\s+can\s+tell)\s+(it\s+won'?t|this\s+won'?t|nothing\s+will)\b/i, weight: 2 },
      { pattern: /\b(won'?t\s+work|will\s+fail|going\s+to\s+be\s+terrible|is\s+doomed)\b/i, weight: 2 },
      { pattern: /\bno\s+point\s+(in\s+)?(even\s+)?(trying|attempting|bothering)\b/i, weight: 3 },
      { pattern: /\b(there'?s?\s+no\s+hope|it'?s?\s+hopeless|nothing\s+can\s+help)\b/i, weight: 2 },
      { pattern: /\bwhat'?s\s+the\s+point\b/i, weight: 1 },
    ],
  },
  {
    id: "catastrophising",
    name: "Catastrophising",
    reframe: "On a scale of 1 to 10, how bad is this truly? And in a year from now, how bad will it be?",
    triggers: [
      { pattern: /\b(worst|most\s+awful|most\s+terrible)\s+thing\s+(that\s+)?(ever|has\s+ever|could)\b/i, weight: 3 },
      { pattern: /\b(my\s+life\s+is\s+)?(ruined|over|destroyed|finished|falling\s+apart|a\s+disaster)\b/i, weight: 3 },
      { pattern: /\b(can'?t\s+handle|can'?t\s+bear|can'?t\s+cope\s+with)\s+(this|it|anymore)\b/i, weight: 2 },
      { pattern: /\b(devastating|catastrophic|unbearable|horrifying|end\s+of\s+the\s+world)\b/i, weight: 2 },
      { pattern: /\beverything\s+is\s+(falling|going)\s+(apart|wrong|to\s+pieces|to\s+hell)\b/i, weight: 3 },
      { pattern: /\b(total|complete|utter)\s+(catastrophe|disaster|nightmare|chaos|mess)\b/i, weight: 2 },
    ],
  },
  {
    id: "emotionalReasoning",
    name: "Emotional reasoning",
    reframe: "Feelings are real: but are they always reliable facts about the world? What would a friend see?",
    triggers: [
      { pattern: /\bi\s+feel\s+(like\s+(a|an)\s+)?(failure|loser|idiot|burden|fraud|fake|worthless|ugly|stupid|unlovable)\b/i, weight: 3 },
      { pattern: /\bi\s+feel\s+(so|really|truly)\s+(worthless|hopeless|broken|useless|disgusting)\b/i, weight: 3 },
      { pattern: /\bif\s+i\s+feel\s+(this\s+way|like\s+this).{0,30}(must\s+be|it\s+is|has\s+to\s+be\s+true)\b/i, weight: 3 },
      { pattern: /\bi\s+(feel|know)\s+i'?m?\s+(terrible|awful|a\s+bad\s+person|broken)\b/i, weight: 2 },
      { pattern: /\bmy\s+feelings?\s+(tell|show|prove)\s+me\b/i, weight: 2 },
    ],
  },
  {
    id: "shouldStatements",
    name: "Should statements",
    reframe: "Where did that \"should\" come from? Is it your rule, or someone else's you adopted?",
    triggers: [
      { pattern: /\bi\s+(should|shouldn'?t|must|mustn'?t|ought\s+to|have\s+to)\s+(?!go\s+to\s+the\s+(doctor|hospital|therapist))/i, weight: 2 },
      { pattern: /\bwhy\s+can'?t\s+i\s+(just|simply|even)\b/i, weight: 2 },
      { pattern: /\bi\s+should\s+(be\s+able\s+to|know\s+better|have\s+known)\b/i, weight: 3 },
      { pattern: /\bi'?m?\s+supposed\s+to\b/i, weight: 2 },
      { pattern: /\bwhat'?s\s+wrong\s+with\s+me\b/i, weight: 2 },
      { pattern: /\bi\s+need\s+to\s+be\s+(better|stronger|different|more)\b/i, weight: 2 },
      { pattern: /\b(people|everyone|you)\s+should\s+(just|always|never|know|understand)\b/i, weight: 2 },
    ],
  },
  {
    id: "personalisation",
    name: "Personalisation",
    reframe: "What other factors might have contributed here, outside of you?",
    triggers: [
      { pattern: /\b(it'?s?|this\s+is)\s+(all\s+)?(my\s+fault)\b/i, weight: 3 },
      { pattern: /\bi\s+(caused|made|caused|ruined|broke)\s+(them|him|her|it|everything|this)\b/i, weight: 2 },
      { pattern: /\bif\s+it\s+wasn'?t\s+for\s+me\b/i, weight: 2 },
      { pattern: /\bi'?m?\s+(the\s+)?(reason|cause|problem|one\s+to\s+blame)\b/i, weight: 3 },
      { pattern: /\bthey('?re|\s+are)\s+upset\s+because\s+of\s+me\b/i, weight: 2 },
      { pattern: /\bi\s+ruined\s+(everything|it|their|the)\b/i, weight: 2 },
      { pattern: /\bblame\s+myself\b/i, weight: 2 },
    ],
  },
];
