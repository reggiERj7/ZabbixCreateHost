from csv import DictReader, QUOTE_MINIMAL
from datetime import datetime as dt
from pyzabbix.api import ZabbixAPI, ZabbixAPIException


class Host:
    def __init__(
        self,
        file,
        url: str,
        user: str,
        password: str,
        template: str,
        type_of_interface: int = 1,
        type_of_host: str = "class",
        port: str = "10050",
    ) -> None:
        self.data = self.parse_data(file)
        self.create_class(
            self.data,
            url,
            user,
            password,
            template,
            type_of_interface=type_of_interface,
            type_of_host=type_of_host,
            port=port,
        )

    @staticmethod
    def parse_data(file) -> list:
        with open(file, mode="r") as file:
            csvFile = DictReader(file, delimiter=";", quoting=QUOTE_MINIMAL)
            return list(csvFile)

    @classmethod
    def auth(cls, url: str, user: str, password: str) -> dict:
        try:
            connect = ZabbixAPI(url)
            connect.login(user=user, password=password)
        except ZabbixAPIException as error:
            Host.create_log_error(error)
        return connect

    @classmethod
    def get_common_data(
        cls,
        template: str,
        type_of_interface: int = 1,
        type_of_host: str = "class",
        port: str = "10050",
    ) -> dict:
        return {
            "template": template,
            "interface": type_of_interface,
            "type_of_host": type_of_host,
            "port": port,
        }

    def check_and_create_host_group(self, name: str, url: str) -> str:
        id_group = url.do_request("hostgroup.get", {"filter": {"name": name}})
        if len(id_group["result"]) == 0:
            url.do_request("hostgroup.create", {"name": name})
            id_group = url.do_request("hostgroup.get", {"filter": {"name": name}})[
                "result"
            ][0]["groupid"]
            return id_group
        return id_group["result"][0]["groupid"]

    @staticmethod
    def create_log(host_info: dict, url: str):
        with open(
            f'{dt.now().strftime("%Y%m%d")}_log.txt', "a", encoding="utf-8"
        ) as file:
            file.write(
                f"Host with address {host_info['ip']} and {host_info['group']} was pushed to {url}"
            )

    @staticmethod
    def create_log_error(error: str):
        with open(
            f'{dt.now().strftime("%Y%m%d")}_error.txt', "a", encoding="utf-8"
        ) as file:
            file.write(f"Error: {error}")

    def create_class(
        self,
        data: dict,
        url: str,
        user: str,
        password: str,
        template: str,
        type_of_interface: int,
        type_of_host: str,
        port: str,
    ) -> None:
        connect = self.auth(url, user, password)
        general_data = self.get_common_data(
            template, type_of_interface, type_of_host, port
        )
        for host in data:
            groupid = self.check_and_create_host_group(host["group"], connect)
            hostname = f"w{host['ip'].split('.')[3]}_gr_id{groupid}"
            try:
                connect.do_request(
                    "host.create",
                    {
                        "host": hostname,
                        "interfaces": [
                            {
                                "type": general_data["interface"],
                                "main": 1,
                                "useip": 1,
                                "ip": host["ip"],
                                "dns": "",
                                "port": general_data["port"],
                            }
                        ],
                        "groups": [{"groupid": groupid}],
                        "templates": [{"templateid": general_data["template"]}],
                    },
                )
                self.create_log(host, url)

            except ZabbixAPIException as error:
                self.create_log_error(error)
