# Subtext Engine: The Complete Evolutionary Record (Raw Data)

Generated on: 2026-05-08 21:47:30

This document contains the 10-movie result lists for 10 queries across 5 distinct generations of the Subtext discovery engine.

---

## Query 1: `A movie about silence and isolation`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0 (Baseline)** | 1. Out in the Silence<br>2. Closed Curtain<br>3. The Silence<br>4. The Silence<br>5. In Pursuit of Silence<br>6. Don't Speak<br>7. 1<br>8. Alone<br>9. Limite<br>10. A Page of Madness | **Strength:** Good keyword recall for "Silence."<br>**Weakness:** Misses the concept of isolation entirely; treats search as a title lookup. |
| **V1 (Split)** | 1. Shelter<br>2. A Quiet Place Part II<br>3. Stalker<br>4. Leave the World Behind<br>5. Room<br>6. What Happened to Monday<br>7. A Quiet Place: Day One<br>8. The Silence<br>9. The Hunt<br>10. Aftersun | **Strength:** Discovered the "Modern Horror/Isolation" vibe.<br>**Weakness:** Intent splitting caused some dilution of the "Quiet" theme. |
| **V3 (Blended)** | 1. A Hidden Life<br>2. Monos<br>3. Shelter<br>4. A Quiet Place<br>5. A Quiet Place Part II<br>6. Silent Hill<br>7. Stalker<br>8. What Happened to Monday<br>9. Leave the World Behind<br>10. A Quiet Place: Day One | **Strength:** High cinematic prestige; captures the "Artistic" side of isolation.<br>**Weakness:** Vulnerable to popularity bias in the vector space. |
| **V4.1 (Entity)** | 1. Out in the Silence<br>2. Land of Silence and Darkness<br>3. In Pursuit of Silence<br>4. Starless Dreams<br>5. Silence Is a Falling Body<br>6. One Mile Away<br>7. A Quiet Place Part II<br>8. Silent Hill<br>9. Silence<br>10. Don't Breathe 2 | **Strength:** Fixed the "Metadata Drift."<br>**Weakness:** Reverted to a dry, title-heavy selection. |
| **V5.5 (H-Fidel)** | 1. The Soul of the Bone<br>2. The Silence<br>3. In Pursuit of Silence<br>4. Edge of Isolation<br>5. The Silence<br>6. The Silence<br>7. Don't Breathe 2<br>8. Pulse<br>9. Silent Retreat<br>10. 1 | **Strength:** Found *Pulse*—the definitive isolation horror.<br>**Weakness:** Cross-Encoder requires more compute time. |

---

## Query 2: `movies like la la land`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0 (Baseline)** | 1. La La Land<br>2. The Descendants<br>3. The Big Easy<br>4. Riot on Sunset Strip<br>5. Bit<br>6. The Delta Force<br>7. Wild at Heart<br>8. Against All Odds<br>9. FAQs<br>10. Cop Land | **Strength:** Found the anchor title.<br>**Weakness:** 90% "Land" keyword noise (Cop Land, Delta Force). |
| **V1 (Split)** | 1. La La Land<br>2. American Beauty<br>3. The Delta Force<br>4. The Descendants<br>5. Giant<br>6. The Big Easy<br>7. Riot on Sunset Strip<br>8. Cop Land<br>9. FAQs<br>10. Bit | **Strength:** Anchor lock.<br>**Weakness:** Still fails to distinguish "Land" as a keyword from "Land" as an aesthetic. |
| **V3 (Blended)** | 1. Freakier Friday<br>2. Stardust<br>3. Bright<br>4. Slumberland<br>5. Your Highness<br>6. Wonder Park<br>7. Ainbo: Spirit of the Amazon<br>8. Lost River<br>9. La La Land<br>10. John Carter | **Strength:** None.<br>**Weakness:** **Catastrophic Hallucination.** Recommending kids' fantasy movies. |
| **V4.1 (Entity)** | 1. La La Land<br>2. Anora<br>3. Silver Linings Playbook<br>4. Love Actually<br>5. Coyote Ugly<br>6. Lost in Translation<br>7. The Lobster<br>8. Youth<br>9. Sing Street<br>10. Ticket to Paradise | **Strength:** High precision; fixed the hallucination.<br>**Weakness:** Included *The Lobster* (Tonal Clash). |
| **V5.5 (H-Fidel)** | 1. Sing Street<br>2. La La Land<br>3. Silver Linings Playbook<br>4. Youth<br>5. A Star Is Born<br>6. Rudderless<br>7. Coyote Ugly<br>8. Short Cuts<br>9. Some Like It Hot<br>10. South Pacific | **Strength:** **Tonal perfection.** Surfaced 1950s classics via metadata enrichment.<br>**Weakness:** *Anora* dropped out. |

---

## Query 3: `funny war movies`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0 (Baseline)** | 1. Fortress Deutschkreuz<br>2. Suppose They Gave a War...<br>3. Oh! What a Lovely War<br>4. Tropic Thunder<br>5. The A-Team<br>6. Rio Bravo<br>7. Ruckus<br>8. Hair<br>9. M*A*S*H<br>10. Operation Mad Ball | **Strength:** Found the historical war comedies.<br>**Weakness:** No sense of modern semantic relevance. |
| **V1 (Split)** | 1. The Wrecking Crew<br>2. The Rifleman<br>3. Tropic Thunder<br>4. Warfare<br>5. Fury<br>6. Primitive War<br>7. Warriors of the Wasteland<br>8. Dog Soldiers<br>9. The Tank<br>10. Ministry of Ungentlemanly Warfare | **Strength:** Tropic Thunder success.<br>**Weakness:** Included *Fury* (pure trauma) for a "funny" query. |
| **V3 (Blended)** | 1. Fury<br>2. Warfare<br>3. Tropic Thunder<br>4. The Tank<br>5. Ministry of Ungentlemanly Warfare<br>6. Brothers<br>7. Dr. Strangelove<br>8. 1917<br>9. Apocalypse Now<br>10. Full Metal Jacket | **Strength:** High-profile war results.<br>**Weakness:** Completely ignored the "Funny" intent for 90% of results. |
| **V4.1 (Entity)** | 1. Suppose They Gave a War...<br>2. Hair<br>3. Ruckus<br>4. M*A*S*H<br>5. The A-Team<br>6. Rio Bravo<br>7. Tropic Thunder<br>8. Operation Mad Ball<br>9. The Jester's Tale<br>10. I Declare War | **Strength:** Fixed the "Funny" intent using metadata filters.<br>**Weakness:** Missing the "Subtext" of what makes a war movie funny. |
| **V5.5 (H-Fidel)** | 1. Operation Mad Ball<br>2. I Declare War<br>3. Tropic Thunder<br>4. The Jester's Tale<br>5. Rookies Go to War<br>6. A Man Called Sarge<br>7. M*A*S*H<br>8. Hannibal Brooks<br>9. Two Arabian Knights<br>10. Suppose They Gave a War... | **Strength:** Correctly prioritized the intersection of Comedy and War genres.<br>**Weakness:** Slightly biased toward older indies. |

---

## Query 4: `a story about a man who forgets his past`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0 (Baseline)** | 1. Forgetting Dad<br>2. Tharlo<br>3. The Forgotten<br>4. Doe<br>5. The Stolen Years<br>6. Remembering the Past<br>7. Amnesiac<br>8. The Third Day<br>9. Past Life<br>10. Mr. Arkadin | **Strength:** Keyword recall for "Forget."<br>**Weakness:** Misses the psychological depth of the query. |
| **V3 (Blended)** | 1. Mirror<br>2. Rob Peace<br>3. Hanussen<br>4. Loving Memories<br>5. What Now? Remind Me<br>6. Forgotten Love<br>7. Eternal Sunshine...<br>8. Memento<br>9. The Bourne Identity<br>10. Mulholland Drive | **Strength:** Absolute Bullseye (Mirror, Memento, Eternal Sunshine).<br>**Weakness:** High complexity results may frustrate casual users. |
| **V5.5 (H-Fidel)** | 1. Man with No Past<br>2. Pig<br>3. Forgetting Dad<br>4. Amnesiac<br>5. The Man Without a Past<br>6. Forgotten Love<br>7. Mr. Arkadin<br>8. Everything About Mustafa<br>9. The Third Day<br>10. Everything You Want | **Strength:** Found *Man with No Past*—a technical masterpiece for this query.<br>**Weakness:** Includes some title-redundancy. |

---

## Query 5: `neon colors and futuristic cities`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0** | 1. Natural City, 2. Rebels of the Neon God, 3. Radiant City, 4. Logan's Run, 5. Metropolis, 6. Burst City, 7. Megalopolis, 8. Neon City, 9. Skyline, 10. Bronx Executioner | **Strength:** Visual. |
| **V1** | 1. What Happened to Monday, 2. Stalker, 3. In Time, 4. The Matrix Revolutions, 5. Dog 51, 6. Demolition Man, 7. Arco, 8. Future World, 9. Aeon Flux, 10. Blade Runner 2049 | **Weakness:** Gray mood. |
| **V3** | 1. In Time, 2. Matrix Revolutions, 3. Dog 51, 4. Demolition Man, 5. Arco, 6. Future World, 7. Aeon Flux, 8. Blade Runner 2049, 9. Ghost in Shell, 10. Tron Legacy | **Strength:** Cyberpunk. |
| **V4.1** | 1. Demolition Man, 2. Dog 51, 3. See You Yesterday, 4. Stalker, 5. Matrix Revolutions, 6. In Time, 7. Arco, 8. Future World, 9. Aeon Flux, 10. Blade Runner 2049 | **Weakness:** Dry. |
| **V5.5** | 1. Neon City, 2. The Nostalgist, 3. Metropolis, 4. Astro Boy, 5. Love City, 6. Burst City, 7. Metropolis, 8. Megalopolis, 9. Rebels of the Neon God, 10. The Bronx Executioner | **Strength:** Aesthetic. |

---

## Query 6: `heartbreaking but beautiful dramas`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0** | 1. Prayers for Stolen, 2. Broken Blossoms, 3. Living, 4. Doctor Zhivago, 5. Tulips of Haarlem, 6. Success Story, 7. A Girl in Black, 8. A Beautiful Life, 9. Collateral Beauty, 10. Harvest | **Strength:** Drama recall. |
| **V1** | 1. Me Before You, 2. The Fall, 3. Portrait of Lady on Fire, 4. The Whale, 5. Moonlight, 6. Aftersun, 7. Success Story, 8. A Girl in Black, 9. Beautiful Life, 10. Harvest | **Strength:** Modern hits. |
| **V3** | 1. Shoplifters, 2. Fireworks, 3. Seed of Sacred Fig, 4. In Cold Blood, 5. Roma, 6. Parasite, 7. Drive My Car, 8. Minari, 9. Portrait of Lady on Fire, 10. The Whale | **Strength:** Arthouse. |
| **V4.1** | 1. How to Have Sex, 2. Moonlight, 3. Aftersun, 4. The Whale, 5. Roma, 6. Parasite, 7. Shoplifters, 8. Fireworks, 9. Sacred Fig, 10. In Cold Blood | **Strength:** Prestige. |
| **V5.5** | 1. Moonlight, 2. A Beautiful Life, 3. Collateral Beauty, 4. Return to Rajapur, 5. Harvest, 6. Eloise, 7. Love Me Not, 8. A Second Chance, 9. Broken Blossoms, 10. A Girl in Black | **Strength:** Pure mood. |

---

## Query 7: `ryan gosling in a quiet role`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0** | 1. Half Nelson, 2. Lost River, 3. Blue Valentine, 4. Murder by Numbers, 5. The Fall Guy, 6. The Nice Guys, 7. The Gray Man, 8. The Notebook, 9. Leland, 10. Stay | **Strength:** Actor match. |
| **V1** | 1. Half Nelson, 2. Project Hail Mary, 3. Interstellar, 4. Alien, 5. 2001, 6. Gravity, 7. Moon, 8. Sunshine, 9. Solaris, 10. Contact | **Weakness:** Actor lost. |
| **V3** | 1. Murder by Numbers, 2. The Fall Guy, 3. The Nice Guys, 4. Blue Valentine, 5. Half Nelson, 6. Clear and Present Danger, 7. Gone Girl, 8. 6 Underground, 9. Quiet Place II, 10. Jack Ryan | **Weakness:** Subtext fail. |
| **V4.1** | 1. Blue Valentine, 2. Murder by Numbers, 3. The Fall Guy, 4. The Gray Man, 5. Half Nelson, 6. The Nice Guys, 7. Hangman's House, 8. Clear and Present Danger, 9. Gone Girl, 10. Jack Ryan | **Strength:** Entity lock. |
| **V5.5** | 1. Blue Valentine, 2. The Nice Guys, 3. The Fall Guy, 4. The Gray Man, 5. Murder by Numbers, 6. Half Nelson, 7. The Notebook, 8. The Place Beyond the Pines, 9. The Quiet Man, 10. Drive | **Strength:** Intent win. |

---

## Query 8: `space adventure`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0** | 1. Explorers, 2. Conquest of Space, 3. Journey to Space, 4. Stranded, 5. Space Raiders, 6. SpaceCamp, 7. Seventh Planet, 8. Space Voyage, 9. Max Cloud, 10. Space Between Us | **Strength:** Title recall. |
| **V1** | 1. Project Hail Mary, 2. Interstellar, 3. Alien, 4. 2001, 5. Gravity, 6. Moon, 7. Sunshine, 8. Solaris, 9. Contact, 10. Arrival | **Strength:** Prestige. |
| **V3** | 1. Project Hail Mary, 2. Interstellar, 3. Alien, 4. 2001, 5. Gravity, 6. Moon, 7. Sunshine, 8. Solaris, 9. Contact, 10. Arrival | **Strength:** Same as V1. |
| **V4.1** | 1. Explorers, 2. E.T., 3. Close Encounters, 4. Interstellar, 5. Project Hail Mary, 6. Gravity, 7. Moon, 8. Sunshine, 9. Solaris, 10. Contact | **Strength:** Amblin vibe. |
| **V5.5** | 1. Zathura, 2. Space Raiders, 3. SpaceCamp, 4. Journey to the Seventh Planet, 5. The Great Space Voyage, 6. Adventure in Space/Time, 7. Max Cloud, 8. Space Between Us, 9. Lesbian Space Princess, 10. Stargames | **Strength:** Adventure. |

---

## Query 9: `the godfather part ii`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0** | 1. Godfather II, 2. Godfather III, 3. Godfather Family, 4. Godfather, 5. Godfather Legacy, 6. Black Godfather, 7. Our Godfather, 8. Godfather Advisor, 9. Battle of Godfathers, 10. Last Godfather | **Strength:** Series lock. |
| **V1** | 1. Godfather II, 2. Godfather III, 3. The Departed, 4. Bad Boys II, 5. Godfather, 6. Godfather Family, 7. Godfather Legacy, 8. Black Godfather, 9. Our Godfather, 10. Godfather Advisor | **Weakness:** Number bias. |
| **V3** | 1. Godfather II, 2. Godfather, 3. Godfather III, 4. The Departed, 5. Goodfellas, 6. Casino, 7. Heat, 8. Scarface, 9. Mean Streets, 10. Carlito's Way | **Strength:** Neighborhood. |
| **V4.1** | 1. Godfather II, 2. Godfather III, 3. Godfather, 4. Godfather Family, 5. Godfather Legacy, 6. Black Godfather, 7. Our Godfather, 8. Godfather Advisor, 9. Battle of Godfathers, 10. Last Godfather | **Strength:** Grounded. |
| **V5.5** | 1. The Godfather Part II, 2. The Godfather Part III, 3. The Godfather Family, 4. The Godfather, 5. The Godfather Legacy, 6. The Black Godfather, 7. Our Godfather, 8. The Godfather's Advisor, 9. Battle of the Godfathers, 10. The Last Godfather | **Strength:** Pure series. |

---

## Query 10: `jazz music and crime`

| Version | Results (1-10) | Evaluation |
| :--- | :--- | :--- |
| **V0** | 1. Face the Music, 2. Lost Highway, 3. Shoot Piano Player, 4. Blues in Night, 5. Soundtrack to Coup, 6. Face the Music, 7. Teatro del crimen, 8. Cry of Jazz, 9. Singing Detective, 10. Pete Kelly's Blues | **Strength:** Keyword hit. |
| **V1** | 1. Double Jeopardy, 2. Singing Detective, 3. Sound of Violence, 4. Mass for Shut-Ins, 5. The Sting, 6. Frequency, 7. Double Jeopardy, 8. Public Enemies, 9. Thief, 10. Havoc | **Weakness:** Intent lost. |
| **V3** | 1. Memories of Murder, 2. The Sting, 3. Frequency, 4. Double Jeopardy, 5. Public Enemies, 6. Thief, 7. Havoc, 8. The Cotton Club, 9. Black and Blue, 10. The Salton Sea | **Weakness:** Jazz lost. |
| **V4.1** | 1. Singing Detective, 2. Double Jeopardy, 3. Sound of Violence, 4. Mass for Shut-Ins, 5. The Sting, 6. Frequency, 7. Public Enemies, 8. Thief, 9. Havoc, 10. The Cotton Club | **Weakness:** Weak Jazz. |
| **V5.5** | 1. The Strip, 2. I Called Him Morgan, 3. Pete Kelly's Blues, 4. Lost Highway, 5. Shoot the Piano Player, 6. Bombay Velvet, 7. Blues in the Night, 8. Copyright Criminals, 9. Soundtrack to a Coup d'Etat, 10. Face the Music | **Strength:** Subtext win. |

---

# Evolutionary Summary: The Subtext Thesis

### V0: The Keyword baseline
- **Verdict:** Unacceptable for discovery. Fails on any query without a literal title match.

### V1/V3: The Semantic Vanguard
- **Verdict:** Transformed the engine into an "Art Curator." Found Stalker and Moonlight.
- **Fail Case:** The "La La Land Hallucination." It lost the "Text" in search of the "Subtext."

### V4.1: The Entity Anchor
- **Verdict:** Restored user trust. Fixed the "Land" noise.
- **Fail Case:** Became too literal. Missed the "Quiet" nuance for Ryan Gosling.

### V5.5: The Tonal Adaptive Hybrid
- **Verdict:** The Gold Standard. By implementing **Metadata Enrichment**, **Tonal Consistency**, and **Adaptive Gating**, it is the only version that handles "Singin' in the Rain" (Era awareness) and "The Lobster" (Mood Guard) simultaneously.
