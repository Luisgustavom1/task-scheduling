DEFAULT_MACHINE_SPEED = 10

def file_size_in_mb(size: int, wms: str) -> float:
  if wms == "Pegasus":
      return size / 1e6  # convert bytes to MB
  else:
      return size / 1e3  # convert KB to MB
  
def convert_machine_speed(speed: int) -> float:
   return speed / 1000 if speed else DEFAULT_MACHINE_SPEED