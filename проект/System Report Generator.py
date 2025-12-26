import platform  # Модуль для получения информации о платформе
import psutil    # Модуль для получения системной информации
import socket    # Модуль для сетевых операций и получения IP-адресов
import datetime  # Модуль для работы с датой и временем
import json      # Модуль для работы с JSON форматом
from typing import Dict, List, Any  # Аннотации типов для лучшей читаемости кода

class SystemReport:
    def __init__(self, fmt: str = "text"):
        """Инициализация объекта отчета с указанием формата вывода"""
        self.fmt = fmt  # Формат отчета: "text" или "json"
        self.info = {}  # Словарь для хранения собранной информации
        self.time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Время создания отчета
    
    def collect(self) -> Dict[str, Any]:
        """Основная функция сбора всей системной информации"""
        self.info = {
            "time": self.time,          # Время создания отчета
            "platform": self._platform(),    # Информация о платформе
            "cpu": self._cpu(),              # Данные о процессоре
            "memory": self._memory(),        # Данные о памяти
            "disks": self._disks(),          # Информация о дисках
            "network": self._network(),      # Сетевые данные
            "processes": self._processes(),  # Список процессов
            "users": self._users(),          # Активные пользователи
            "boot": self._boot(),            # Время загрузки системы
            "sensors": self._sensors()       # Данные с датчиков
        }
        return self.info
    
    def _platform(self) -> Dict[str, str]:
        """Сбор информации об операционной системе и хосте"""
        return {
            "system": platform.system(),      # Название ОС (Linux, Windows, macOS)
            "release": platform.release(),    # Версия релиза ОС
            "version": platform.version(),    # Полная версия ОС
            "host": socket.gethostname(),     # Имя хоста компьютера
            "ip": socket.gethostbyname(socket.gethostname())  # Основной IP-адрес
        }
    
    def _cpu(self) -> Dict[str, Any]:
        """Сбор данных о процессоре: ядра, частота, загрузка"""
        freq = psutil.cpu_freq()  # Получение информации о частоте
        return {
            "physical_cores": psutil.cpu_count(logical=False),  # Физические ядра
            "logical_cores": psutil.cpu_count(logical=True),    # Логические ядра
            "freq": f"{freq.current:.0f} MHz" if freq else "N/A",  # Текущая частота
            "usage": psutil.cpu_percent(interval=0.5),          # Общая загрузка CPU
            "per_cpu": psutil.cpu_percent(interval=0.5, percpu=True)  # Загрузка по ядрам
        }
    
    def _memory(self) -> Dict[str, Any]:
        """Анализ использования оперативной памяти и swap"""
        vmem = psutil.virtual_memory()  # Оперативная память
        swap = psutil.swap_memory()     # Файл подкачки
        return {
            "total_ram": f"{vmem.total / (1024**3):.1f} GB",      # Всего ОЗУ
            "used_ram": f"{vmem.used / (1024**3):.1f} GB",        # Использовано ОЗУ
            "ram_percent": vmem.percent,                          # Процент использования
            "swap": f"{swap.used / (1024**3):.1f}/{swap.total / (1024**3):.1f} GB"  # Swap
        }
    
    def _disks(self) -> List[Dict[str, Any]]:
        """Сбор информации о дисковых накопителях и разделах"""
        disks = []
        for part in psutil.disk_partitions():  # Перебор всех разделов
            try:
                use = psutil.disk_usage(part.mountpoint)  # Использование диска
                disk_info = {
                    "device": part.device,      # Имя устройства (/dev/sda1, C:)
                    "mountpoint": part.mountpoint,  # Точка монтирования (/home, C:\)
                    "fstype": part.fstype,      # Тип файловой системы (NTFS, ext4)
                    "total": f"{use.total / (1024**3):.1f} GB",  # Общий объем
                    "used": f"{use.used / (1024**3):.1f} GB",    # Использовано
                    "free": f"{use.free / (1024**3):.1f} GB",    # Свободно
                    "percent": use.percent                         # Процент использования
                }
                
                # Добавление статистики ввода-вывода если доступно
                try:
                    io = psutil.disk_io_counters(perdisk=True).get(part.device.replace("\\", "").replace("/", ""), None)
                    if io:
                        disk_info["read_bytes"] = f"{io.read_bytes / (1024**2):.1f} MB"
                        disk_info["write_bytes"] = f"{io.write_bytes / (1024**2):.1f} MB"
                except:
                    pass
                    
                disks.append(disk_info)
            except (PermissionError, OSError):
                continue  # Пропуск недоступных разделов
        return disks
    
    def _network(self) -> Dict[str, Any]:
        """Сбор сетевой статистики и информации об интерфейсах"""
        io = psutil.net_io_counters()           # Общая сетевая статистика
        net_if_addrs = psutil.net_if_addrs()    # Адреса сетевых интерфейсов
        net_if_stats = psutil.net_if_stats()    # Статус интерфейсов
        
        interfaces = {}
        for iface, addrs in net_if_addrs.items():  # Анализ каждого интерфейса
            ip_addresses = []  # Список IP-адресов интерфейса
            mac_address = None  # MAC-адрес
            
            # Обработка всех адресов интерфейса
            for addr in addrs:
                if addr.family == socket.AF_INET:  # IPv4 адреса
                    ip_addresses.append(f"IPv4: {addr.address}/{addr.netmask}")
                elif addr.family == socket.AF_INET6:  # IPv6 адреса
                    ip_addresses.append(f"IPv6: {addr.address}")
                elif addr.family == psutil.AF_LINK:  # MAC-адрес
                    mac_address = addr.address
            
            # Получение статуса интерфейса
            stats = {}
            if iface in net_if_stats:
                stat = net_if_stats[iface]
                stats = {
                    "is_up": "UP" if stat.isup else "DOWN",  # Состояние интерфейса
                    "speed": f"{stat.speed} Mbps" if stat.speed > 0 else "N/A",  # Скорость
                    "mtu": stat.mtu  # Maximum Transmission Unit
                }
            
            interfaces[iface] = {
                "ip_addresses": ip_addresses,  # Список IP-адресов
                "mac": mac_address,            # MAC-адрес
                "stats": stats                 # Статус интерфейса
            }
        
        return {
            "bytes_sent": f"{io.bytes_sent / (1024**2):.1f} MB",      # Отправлено данных
            "bytes_recv": f"{io.bytes_recv / (1024**2):.1f} MB",      # Получено данных
            "packets_sent": io.packets_sent,                          # Отправлено пакетов
            "packets_recv": io.packets_recv,                          # Получено пакетов
            "interfaces": interfaces                                   # Данные по интерфейсам
        }
    
    def _processes(self) -> List[Dict[str, Any]]:
        """Получение списка топ-8 процессов по использованию памяти"""
        procs = []
        # Итерация по всем процессам
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = p.info  # Основная информация о процессе
                # Добавление информации об использовании памяти в МБ
                info['memory_mb'] = psutil.Process(p.info['pid']).memory_info().rss / (1024**2)
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue  # Пропуск недоступных процессов
        
        # Сортировка по использованию памяти (по убыванию)
        procs.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
        return procs[:8]  # Возврат топ-8 процессов
    
    def _users(self) -> List[Dict[str, Any]]:
        """Получение списка активных пользователей в системе"""
        users = []
        for user in psutil.users():  # Перебор всех активных пользователей
            users.append({
                "name": user.name,      # Имя пользователя
                "host": user.host,      # С какого хоста подключен
                "started": datetime.datetime.fromtimestamp(user.started).strftime("%H:%M:%S")  # Время входа
            })
        return users
    
    def _boot(self) -> str:
        """Получение времени последней загрузки системы"""
        return datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    
    def _sensors(self) -> Dict[str, Any]:
        """Получение данных с температурных датчиков (если доступно)"""
        try:
            temps = psutil.sensors_temperatures()  # Температурные датчики
            sensors = {}
            if temps:
                for name, entries in temps.items():  # Обработка каждого датчика
                    sensors[name] = [{"current": entry.current} for entry in entries[:2]]
            return sensors
        except AttributeError:
            return {"info": "N/A"}  # Если датчики недоступны
    
    def text_report(self) -> str:
        """Формирование текстового отчета в удобочитаемом формате"""
        report = [
            "=" * 60,
            f"СИСТЕМНЫЙ ОТЧЕТ - {self.time}",
            "=" * 60
        ]
        
        # Добавление информации о платформе
        report.extend([
            "\nПЛАТФОРМА:",
            "-" * 40,
            f"Система: {self.info['platform']['system']} {self.info['platform']['release']}",
            f"Версия: {self.info['platform']['version']}",
            f"Хост: {self.info['platform']['host']}",
            f"IP-адрес: {self.info['platform']['ip']}"
        ])
        
        # Добавление информации о процессоре
        cpu = self.info['cpu']
        report.extend([
            "\nПРОЦЕССОР:",
            "-" * 40,
            f"Ядра: {cpu['physical_cores']} физических, {cpu['logical_cores']} логических",
            f"Частота: {cpu['freq']}",
            f"Загрузка: {cpu['usage']}%",
            f"По ядрам: {', '.join([f'{p}%' for p in cpu['per_cpu']])}"
        ])
        
        # Добавление информации о памяти
        mem = self.info['memory']
        report.extend([
            "\nПАМЯТЬ:",
            "-" * 40,
            f"ОЗУ: {mem['used_ram']} / {mem['total_ram']} ({mem['ram_percent']}%)",
            f"SWAP: {mem['swap']}"
        ])
        
        # Добавление информации о дисках
        report.extend(["\nДИСКОВЫЕ НАКОПИТЕЛИ:", "-" * 40])
        for i, disk in enumerate(self.info['disks'], 1):
            disk_info = [
                f"{i}. {disk['device']} → {disk['mountpoint']}",
                f"   Тип: {disk['fstype']}, Всего: {disk['total']}",
                f"   Использовано: {disk['used']} ({disk['percent']}%), Свободно: {disk['free']}"
            ]
            if 'read_bytes' in disk:
                disk_info.append(f"   Чтение: {disk['read_bytes']}, Запись: {disk['write_bytes']}")
            report.extend(disk_info)
        
        # Добавление сетевой информации
        net = self.info['network']
        report.extend([
            "\nСЕТЕВЫЕ ИНТЕРФЕЙСЫ:",
            "-" * 40,
            f"Отправлено: {net['bytes_sent']}, Получено: {net['bytes_recv']}",
            f"Пакеты: отправлено {net['packets_sent']}, получено {net['packets_recv']}"
        ])
        
        # Добавление информации о каждом сетевом интерфейсе
        for iface, info in net['interfaces'].items():
            if info['ip_addresses']:
                report.append(f"\n{iface}:")
                if info['mac']:
                    report.append(f"  MAC: {info['mac']}")
                for ip in info['ip_addresses'][:2]:  # Показываем первые 2 адреса
                    report.append(f"  {ip}")
                if info['stats']:
                    report.append(f"  Статус: {info['stats']['is_up']}, "
                                 f"Скорость: {info['stats']['speed']}")
        
        # Добавление информации о процессах
        report.extend(["\nТОП-8 ПРОЦЕССОВ:", "-" * 40])
        for i, proc in enumerate(self.info['processes'], 1):
            report.append(f"{i}. {proc['name'][:20]:20} "
                         f"PID:{proc['pid']:6} "
                         f"CPU:{proc['cpu_percent']:5.1f}% "
                         f"MEM:{proc['memory_percent']:5.1f}%")
        
        # Добавление информации о пользователях
        if self.info['users']:
            report.extend(["\nАКТИВНЫЕ ПОЛЬЗОВАТЕЛИ:", "-" * 40])
            for user in self.info['users']:
                report.append(f"{user['name']} с {user['host']} (с {user['started']})")
        
        # Добавление времени загрузки и завершение отчета
        report.extend([
            f"\nВРЕМЯ ЗАГРУЗКИ: {self.info['boot']}",
            "=" * 60
        ])
        
        return "\n".join(report)
    
    def json_report(self) -> str:
        """Формирование отчета в формате JSON"""
        return json.dumps(self.info, indent=2, default=str)
    
    def save(self, fname: str = None) -> str:
        """Сохранение отчета в файл"""
        if not fname:
            fname = f"system_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        fname += ".json" if self.fmt == "json" else ".txt"
        
        # Выбор содержимого в зависимости от формата
        content = self.json_report() if self.fmt == "json" else self.text_report()
        
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(content)
        return fname

def main():
    """Основная функция программы с обработкой аргументов командной строки"""
    import argparse
    parser = argparse.ArgumentParser(description="Генератор системных отчетов")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Формат отчета (text или json)")
    parser.add_argument("--output", "-o", help="Имя выходного файла")
    parser.add_argument("--print", "-p", action="store_true",
                       help="Вывести отчет в консоль")
    
    args = parser.parse_args()
    
    try:
        report = SystemReport(args.format)  # Создание объекта отчета
        report.collect()  # Сбор системной информации
        
        # Вывод отчета в консоль если указан флаг --print
        if args.print:
            print(report.json_report() if args.format == "json" else report.text_report())
        
        # Сохранение отчета в файл
        if args.output or not args.print:
            fname = report.save(args.output)
            print(f"Отчет сохранен: {fname}")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
