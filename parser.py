import struct
import os


class ZipParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file = None
        self.central_directory = []

    def _read_end_of_central_directory(self):
        
        self.file.seek(-22, os.SEEK_END)
        signature = self.file.read(4)

        if signature != b'PK\x05\x06':
            raise ValueError("Nie znaleziono końca centralnego katalogu.")

        
        data = self.file.read(18)
        _, _, _, self.num_entries, _, self.central_dir_offset = struct.unpack("<4H2L", data)

    def _read_central_directory(self):
       
        self.file.seek(self.central_dir_offset)
        for _ in range(self.num_entries):
            signature = self.file.read(4)

            if signature != b'PK\x01\x02':
                raise ValueError("Niepoprawny wpis centralnego katalogu.")

            
            header_data = self.file.read(42)
            (
                _, _, _, _, _, _, compressed_size, uncompressed_size,
                file_name_length, extra_field_length, file_comment_length,
                _, _, local_header_offset
            ) = struct.unpack("<4H4L2H4L", header_data)

            file_name = self.file.read(file_name_length).decode('utf-8')
            self.file.seek(extra_field_length + file_comment_length, os.SEEK_CUR)

            self.central_directory.append({
                "file_name": file_name,
                "compressed_size": compressed_size,
                "uncompressed_size": uncompressed_size,
                "local_header_offset": local_header_offset,
            })

    def _read_local_file(self, entry):
       
        self.file.seek(entry['local_header_offset'])
        signature = self.file.read(4)

        if signature != b'PK\x03\x04':
            raise ValueError(f"Nie znaleziono lokalnego nagłówka pliku dla {entry['file_name']}.")

        
        header_data = self.file.read(26)
        file_name_length, extra_field_length = struct.unpack("<2H", header_data[22:26])
        self.file.seek(file_name_length + extra_field_length, os.SEEK_CUR)

       
        compressed_data = self.file.read(entry['compressed_size'])

        return compressed_data

    def parse(self):
        """
        Główna metoda parsująca plik ZIP.
        """
        with open(self.file_path, 'rb') as self.file:
            self._read_end_of_central_directory()
            self._read_central_directory()

    def list_files(self):
       
        for entry in self.central_directory:
            print(f"{entry['file_name']} (skompresowany: {entry['compressed_size']} B, nieskompresowany: {entry['uncompressed_size']} B)")

    def extract_file(self, file_name):
        
        for entry in self.central_directory:
            if entry['file_name'] == file_name:
                compressed_data = self._read_local_file(entry)
                return compressed_data
        raise FileNotFoundError(f"Plik {file_name} nie został znaleziony w archiwum.")



if __name__ == "__main__":
    zip_file = "example.zip"
    parser = ZipParser(zip_file)
    parser.parse()
    parser.list_files()

    # Wyodrębnianie konkretnego pliku
    try:
        file_name = "example.txt"
        data = parser.extract_file(file_name)
        print(f"Zawartość pliku {file_name}:")
        print(data.decode('utf-8'))
    except FileNotFoundError as e:
        print(e)
