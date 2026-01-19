resource "proxmox_virtual_environment_vm" "factory_vm" {
  for_each = var.vms
  scsi_hardware = "virtio-scsi-single"
  node_name = each.value.target_node
  vm_id     = each.value.id
  name      = each.key

  
  clone {
    vm_id = 9213 
    full  = true
  }

  agent {
    enabled = false
  }

  cpu {
    cores = each.value.cores
    type  = "host"
  }

  memory {
    dedicated = each.value.memory
  }

  disk {
    datastore_id = "Cible_NFS"
    interface    = "scsi0"
    size         = each.value.disk_size
    file_format  = "raw"
    iothread     = true
  }

  network_device {
    bridge = "vmbr_ay"
    model  = "virtio"
  }

  initialization {
    datastore_id = "Cible_NFS"
    ip_config {
      ipv4 {
        address = each.value.ip_cidr
        gateway = each.value.gateway
      }
    }

    user_account {
      keys = [var.ssh_public_key]
      username = "admin"
    }
  }

  lifecycle {
    ignore_changes = [
      initialization,
    ]
  }
}
