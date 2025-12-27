from src.base_api_client import APISettings
from src.wb_client import WBSettings, WBClient

def main():
    api = APISettings(
        base_url="https://api.worldbank.org/v2",
        batch_size=1000,
    )
    wb_settings = WBSettings(
        countries=["USA", "CAN", "GBR"],  # Коды стран
        indicators=["NY.GDP.MKTP.CD", "SP.POP.TOTL"],  # GDP и население
        date_intervals=["2010:2020"],  # Период 2010-2020
        api=api
    )
    client = WBClient(wb_settings)
    with client:
        print(f"Клиент подключен: {client.is_connected}")
        print(f"Будут запрошены индикаторы: {client.indicators}")
        print(f"Для стран: {client.countries}")
        print("=" * 50)

        # Получаем данные
        count = 0
        for data_point in client.fetch_all():
            count += 1
            print(f"Точка данных {count}:")
            print(f"  Страна: {data_point.get('country', {}).get('value', 'N/A')}")
            print(f"  Индикатор: {data_point.get('indicator', {}).get('value', 'N/A')}")
            print(f"  Год: {data_point.get('date', 'N/A')}")
            print(f"  Значение: {data_point.get('value', 'N/A')}")
            print("-" * 30)

            # Ограничим вывод для примера
            if count >= 10:
                print("Выведено 10 записей, останавливаемся...")
                break

        print(f"\nВсего получено записей: {count}")

if __name__ == "__main__":
    main()