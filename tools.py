import os
import requests
from dotenv import load_dotenv
from langchain.tools import tool
load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
YAHOO_API_KEY = os.getenv("YAHOO_FINANCE_API_KEY")

@tool
def tool1_weather(query: str) -> str:
    """
    Weather Tool: Handles current, forecast, yesterday's weather, or city comparison based on user query.
    Automatically extracts intent and cities from input.
    """
    try:
        import re
        from datetime import datetime, timedelta

        original_query = query
        q = query.lower()

        is_forecast = "forecast" in q or "next 7" in q or "7-day" in q
        is_yesterday = "yesterday" in q
        is_compare = "compare" in q or (" and " in q and "weather" in q)


        # Simple and reliable city extractor based on known format
        city_pattern = re.findall(r"(?:in|at|of|for)?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", query)
        city_names = list(dict.fromkeys([c.strip() for c in city_pattern if c.strip()])) or [query.strip()]

        if is_compare and len(city_names) >= 2:
            results = []
            for city in city_names[:2]:
                url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
                data = requests.get(url).json()
                temp = data["current"]["temp_c"]
                condition = data["current"]["condition"]["text"]
                results.append(f"{city}: {temp}°C, {condition}")
            return f"🌤️ City Comparison:\n" + "\n".join(results)

        city = city_names[0]

        # Yesterday’s weather
        if is_yesterday:
            yday = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            url = f"http://api.weatherapi.com/v1/history.json?key={WEATHER_API_KEY}&q={city}&dt={yday}"
            res = requests.get(url)
            data = res.json()
            avg_temp = data["forecast"]["forecastday"][0]["day"]["avgtemp_c"]
            condition = data["forecast"]["forecastday"][0]["day"]["condition"]["text"]
            return f"📆 Yesterday’s Weather in {city} ({yday}): {avg_temp}°C, {condition}"

        # 7-Day Forecast
        elif is_forecast:
            url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=7"
            data = requests.get(url).json()
            result = f"📅 7-Day Forecast for {city.title()}:\n"
            # for day in data["forecast"]["forecastday"]:
            #     date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
            #     formatted_date = date_obj.strftime("%a, %d %b")
            #     result += f"{formatted_date}: {day['day']['condition']['text']}, {day['day']['avgtemp_c']}°C\n"
            # return result.strip()

            # for day in data["forecast"]["forecastday"]:
            #     date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
            #     formatted_date = date_obj.strftime("%A, %d %B %Y")  
            #     condition = day["day"]["condition"]["text"]
            #     temp = day["day"]["avgtemp_c"]
            #     result += f"{formatted_date}: {condition}, Avg Temp: {temp}°C\n"
            # for day in data["forecast"]["forecastday"]:
            #     date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
            #     formatted_date = date_obj.strftime("%a, %d %b %Y")  # Example: Wed, 23 Jul 2025
            #     condition = day["day"]["condition"]["text"]
            #     avg_temp = day["day"]["avgtemp_c"]
            #     result += f"{formatted_date}: {condition}, Avg Temp: {avg_temp}°C\n"
            for day in data["forecast"]["forecastday"]:
                date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
                # formatted_date = date_obj.strftime("%a, %d %b %Y")  # e.g., Wed, 23 Jul
                formatted_date = date_obj.strftime("%a, %d %b %Y")

                avg_temp = day["day"]["avgtemp_c"]
                result += f"{formatted_date}: {avg_temp}°C\n"  # <-- Newline added here

            return result.strip()

        else:
            url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
            data = requests.get(url).json()
            temp = data["current"]["temp_c"]
            condition = data["current"]["condition"]["text"]
            return f"{temp}°C, {condition}"

    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def tool2_stock(query: str) -> str:
    """
    Extracts the company name from a natural query and fetches the stock price dynamically via Yahoo Finance API.
    """
    import requests
    import yfinance as yf
    import re

    try:
        match = re.search(r"(?:price for|stock price for|stock of)\s+(.+)", query.lower())
        search_term = match.group(1).strip() if match else query.strip()

        headers = {"User-Agent": "Mozilla/5.0"}
        search_url = f"https://query1.finance.yahoo.com/v1/finance/search?q={search_term}"
        response = requests.get(search_url, headers=headers, timeout=10)
        data = response.json()

        quotes = data.get("quotes", [])
        if not quotes:
            return f"❌ No matching stock symbol found for '{search_term}'."

        # Prefer Indian NSE/BSE listing
        preferred = [q.get("symbol") for q in quotes if q.get("symbol", "").endswith((".NS", ".BO"))]
        symbol = preferred[0] if preferred else quotes[0].get("symbol")

        if not symbol:
            return f"⚠️ No ticker symbol found for '{search_term}'."

        ticker = yf.Ticker(symbol)
        price = ticker.fast_info.get("last_price") or ticker.info.get("regularMarketPrice")
        currency = ticker.fast_info.get("currency", "INR")

        symbol_map = {"INR": "₹", "USD": "$", "EUR": "€"}
        symbol_char = symbol_map.get(currency, "")

        if price:
            return f"📈 Stock: {symbol} ({currency})\n💰 Current Price: {symbol_char}{price}"
        else:
            return f"⚠️ Price not available for '{symbol}'."

    except Exception as e:
        return f"❌ Error: {str(e)}"

@tool
def tool3_general_qa(question: str) -> str:
    """Tool3: Answer general knowledge questions like 'What is AI?' or 'Who is the PM of India?'."""
    return f"(LLM will answer this): {question}"