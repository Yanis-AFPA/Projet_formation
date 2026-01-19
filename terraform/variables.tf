variable "proxmox_api_url" {
  description = "URL de l'API Proxmox"
  type        = string
}

variable "proxmox_api_token_id" {
  description = "ID du token API Proxmox"
  type        = string
}

variable "proxmox_api_token_secret" {
  description = "Secret du token API Proxmox"
  type        = string
  sensitive   = true
}

variable "vms" {
  description = "Map des VMs à déployer"
  type = map(object({
    id          = number
    target_node = string
    template    = string
    cores       = number
    memory      = number
    disk_size   = number
    ip_cidr     = string
    gateway     = string
    tags        = string
  }))
}

variable "ssh_public_key" {
  description = "Clé publique SSH pour les VMs"
  type        = string
}
