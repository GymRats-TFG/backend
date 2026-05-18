import httpx
from fastapi import HTTPException

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
# Nominatim exige un User-Agent identificativo.
USER_AGENT = "GymRats-TFG/1.0 (gymratstfg@gmail.com)"

async def forward_geocode(street: str, number: str, city: str, country: str) -> tuple[float, float]:
    query = f"{number} {street}, {city}, {country}"
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{NOMINATIM_URL}/search",
            params={"q": query, "format": "json", "limit": 1, "addressdetails": 1},
            headers={"User-Agent": USER_AGENT}
        )
        data = res.json()
        if not data:
            raise HTTPException(status_code=404, detail="No se encontró la ubicación. Revisa la dirección.")
        
        return float(data[0]["lat"]), float(data[0]["lon"])

async def reverse_geocode(lat: float, lon: float) -> str:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{NOMINATIM_URL}/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": USER_AGENT}
        )
        data = res.json()
        if "error" in data:
            return "Ubicación no disponible"
            
        addr = data.get("address", {})
        road = addr.get("road", "")
        house_number = addr.get("house_number", "")
        city = addr.get("city") or addr.get("town") or addr.get("village", "")
        country = addr.get("country", "")
        
        # Formatear limpio: "Calle Mayor 12, Madrid, España"
        return f"{road} {house_number}".strip() + (f", {city}" if city else "") + (f", {country}" if country else "")