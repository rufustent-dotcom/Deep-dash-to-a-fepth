# Using Pydantic types
response = client.models.generate_content(
    model='gemini-2.5-flash',
    config=types.GenerateContentConfig(temperature=0.7)
)