from eth_vertigo.core.campaign import BaseCampaign
from typing import List
from eth_vertigo.mutator.mutator import Mutator
from pathlib import Path
from eth_vertigo.core.network import NetworkPool
from json import loads


class FoundryCampaign(BaseCampaign):
    def __init__(
            self,
            foundry_command: List[str],
            project_directory: Path,
            mutators: List[Mutator],
            network_pool: NetworkPool,
            filters=None,
            suggesters=None
    ):
        from eth_vertigo.interfaces.foundry.tester import FoundryTester
        from eth_vertigo.interfaces.foundry.compile import FoundryCompiler
        from eth_vertigo.interfaces.foundry.mutator import FoundrySourceFile

        compiler = FoundryCompiler(foundry_command)
        tester = FoundryTester(foundry_command, str(project_directory), compiler)
        source_file_builder = lambda ast, full_path: FoundrySourceFile(ast, full_path)

        super().__init__(
            project_directory=project_directory,
            mutators=mutators,
            network_pool=network_pool,

            compiler=compiler,
            tester=tester,
            source_file_builder=source_file_builder,

            filters=filters,
            suggesters=suggesters
        )

    def _get_sources(self):
        """ Implements basic mutator file discovery """
        contracts_dir = self.project_directory / "out" #/ "contracts"
        if not contracts_dir.exists():
            self.compiler.run_compilation(str(self.project_directory))

        contract_directories = []
        def explore_contracts(directory: Path):
            for item in directory.iterdir():
                # TODO: Hardcode for now because foundry compiles too many files in the out/ directory
                if item.name == "Counter.sol" and item.name.endswith(".sol"):
                    contract_directories.append(item)
                elif item.is_dir():
                    explore_contracts(item)

        explore_contracts(contracts_dir)

        for contract_dir in contract_directories:
            for contract in [c for c in contract_dir.iterdir()]:
                contract = loads(contract.read_text("utf-8"))

                ast = contract["ast"]
                absolute_path = self.project_directory / ast["absolutePath"]
                yield self.source_file_builder(ast, absolute_path)
            #for contract in [c for c in contract_dir.iterdir() if "dbg.json" not in c.name]:

                #yield self.source_file_builder(ast, absolute_path)
                '''
                dbg_json = contract_dir / contract.name.replace('.json', '.dbg.json')

                contract = loads(contract.read_text("utf-8"))
                dbg = loads(dbg_json.read_text("utf-8"))

                source_name = contract["sourceName"]
                build_info_file = contract_dir / dbg["buildInfo"]
                build_info = loads(build_info_file.read_text("utf-8"))

                ast = build_info["output"]["sources"][source_name]["ast"]
                absolute_path = self.project_directory / ast["absolutePath"]

                yield self.source_file_builder(ast, absolute_path)
                '''
