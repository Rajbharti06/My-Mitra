# MyMitra

MyMitra is an AI companion designed to talk like a real person, offering a private and safe space where people can share their thoughts.

It combines fine-tuned conversational AI with:

- **Multi-Stage CBT Agent**: Uses Cognitive Behavioral Therapy (CBT) techniques in steps (awareness → reflection → reframing → action). Helps users challenge negative thoughts, manage stress, and build resilience.
- **Long-Term Memory**: Remembers past conversations in a secure way. Builds a personalized connection like a friend or mentor who really knows you.
- **Evidence-Based Insights**: Tracks moods, patterns, and habits. Provides science-backed suggestions, not random “feel-good” advice.
- **Focused on Gen Z, Millennials & Gen Alpha**: Language, tone, and style adapted to younger generations. Works best for people balancing studies, careers, personal growth, and emotional challenges.
- **Privacy First**: Fully encrypted; even the app admin can’t read chats. Offline by default, with optional API integrations.

## Mission Statement

“MyMitra is a private AI companion that talks like a real person, combining CBT techniques, long-term memory, and evidence-based insights to support Gen Z, Millennials, and Gen Alpha in their emotional well-being and personal growth.”

## Project Structure

- `src/core_ai`: Contains the core AI system components, including model fine-tuning, CBT logic, and long-term memory implementation.
- `src/app_layer`: Contains the application layer components, including the Flutter frontend, FastAPI/Node.js backend, and database setup.
- `src/trust_safety`: Contains components related to trust and safety, such as chat encryption, secure login, and data privacy features.