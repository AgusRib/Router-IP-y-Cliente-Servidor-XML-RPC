/**********************************************************************
 * file:  sr_router.c
 *
 * Descripción:
 *
 * Este archivo contiene todas las funciones que interactúan directamente
 * con la tabla de enrutamiento, así como el método de entrada principal
 * para el enrutamiento.
 *
 **********************************************************************/

#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>

#include "sr_if.h"
#include "sr_rt.h"
#include "sr_router.h"
#include "sr_protocol.h"
#include "sr_arpcache.h"
#include "sr_utils.h"


/*---------------------------------------------------------------------
 * Method: sr_init(void)
 * Scope:  Global
 *
 * Inicializa el subsistema de enrutamiento
 *
 *---------------------------------------------------------------------*/

void sr_init(struct sr_instance* sr)
{
    assert(sr);

    /* Inicializa la caché y el hilo de limpieza de la caché */
    sr_arpcache_init(&(sr->cache));

    /* Inicializa los atributos del hilo */
    pthread_attr_init(&(sr->attr));
    pthread_attr_setdetachstate(&(sr->attr), PTHREAD_CREATE_JOINABLE);
    pthread_attr_setscope(&(sr->attr), PTHREAD_SCOPE_SYSTEM);
    pthread_attr_setscope(&(sr->attr), PTHREAD_SCOPE_SYSTEM);
    pthread_t thread;

    /* Hilo para gestionar el timeout del caché ARP */
    pthread_create(&thread, &(sr->attr), sr_arpcache_timeout, sr);

} /* -- sr_init -- */

/* Envía un paquete ICMP de error */
void sr_send_icmp_error_packet(uint8_t type,
                              uint8_t code,
                              struct sr_instance *sr,
                              uint32_t ipDst,
                              uint8_t *ipPacket)
{
 assert(sr);
    assert(ipPacket);

    struct sr_ip_hdr *orig_ip_hdr = (struct sr_ip_hdr *)ipPacket;
    struct sr_rt *rt_entry = sr_prefijo_mas_largo(sr, ipDst);
    if (!rt_entry) {
      printf("$$$ -> ERROR no se encontró entrada en la tabla de reenvío.\n");
        return;
    }

    struct sr_if *interfaz_salida = sr_get_interface(sr, rt_entry->interface);
    if (!interfaz_salida) {
      printf("$$$ -> ERROR no se encontró la interfaz de salida.\n");
        return;
    }


    uint32_t next_hop_ip = (rt_entry->gw.s_addr != 0) ? rt_entry->gw.s_addr : ipDst;

  
    uint16_t icmp_len = 0;
    uint8_t *icmp_packet = NULL;

    if (type == 3) {
        icmp_len = sizeof(sr_icmp_t3_hdr_t);
        icmp_packet = malloc(icmp_len);
        if (!icmp_packet) { return; }

        sr_icmp_t3_hdr_t *icmp3 = (sr_icmp_t3_hdr_t *)icmp_packet;
        icmp3->icmp_type = type;
        icmp3->icmp_code = code;
        icmp3->unused = 0;
        icmp3->next_mtu = 0;
        memcpy(icmp3->data, ipPacket, ICMP_DATA_SIZE);
        icmp3->icmp_sum = 0;
        icmp3->icmp_sum = icmp3_cksum(icmp3, sizeof(sr_icmp_t3_hdr_t));
    } else if (type == 11) {
        icmp_len = sizeof(sr_icmp_t11_hdr_t);
        icmp_packet = malloc(icmp_len);
        if (!icmp_packet) { return; }

        sr_icmp_t11_hdr_t *icmp11 = (sr_icmp_t11_hdr_t *)icmp_packet;
        icmp11->icmp_type = type;
        icmp11->icmp_code = code;
        icmp11->unused = 0;
        memcpy(icmp11->data, ipPacket, ICMP_DATA_SIZE);
        icmp11->icmp_sum = 0;
        icmp11->icmp_sum = icmp11_cksum(icmp11,  sizeof(sr_icmp_t11_hdr_t));
    } else {
        return;
    }

    /* Armar IP header */
    uint8_t ip_nupacket[sizeof(sr_ip_hdr_t) + icmp_len];
    struct sr_ip_hdr *ip_hdr = (struct sr_ip_hdr *)ip_nupacket;
    ensamblar_ip_header(ip_hdr, interfaz_salida->ip, orig_ip_hdr->ip_src,
                    sizeof(ip_nupacket), ip_protocol_icmp);
    memcpy(ip_nupacket + sizeof(sr_ip_hdr_t), icmp_packet, icmp_len);

    /* Resolver MAC destino (ARP) */
    struct sr_arpentry *entry = sr_arpcache_lookup(&sr->cache, next_hop_ip);
    if (entry) {
        uint8_t paquete_completo[sizeof(sr_ethernet_hdr_t) + sizeof(ip_nupacket)];
         struct sr_ethernet_hdr *eth_hdr = (struct sr_ethernet_hdr *)paquete_completo;

        ensamblar_eth_header(eth_hdr, interfaz_salida->addr, entry->mac, ethertype_ip);
        memcpy(paquete_completo + sizeof(sr_ethernet_hdr_t), ip_nupacket, sizeof(ip_nupacket));

        sr_send_packet(sr, paquete_completo, sizeof(paquete_completo), interfaz_salida->name);
        free(entry);
    } else {
        /* Encolar un frame ETHERNET + IP/ICMP completo. La cola y
         * sr_arp_reply_send_pending_packets esperan que el buffer tenga
         * un encabezado Ethernet para poder sobrescribir las MACs cuando
         * llegue la respuesta ARP. */
        int full_len = sizeof(sr_ethernet_hdr_t) + sizeof(ip_nupacket);
        uint8_t *full_pkt = (uint8_t *)malloc(full_len);
        if (full_pkt) {
            sr_ethernet_hdr_t *eth_pending = (sr_ethernet_hdr_t *)full_pkt;
            uint8_t zero_mac[ETHER_ADDR_LEN];
            memset(zero_mac, 0x00, ETHER_ADDR_LEN);

            /* src = interfaz_salida->addr, dst = 00:00:.. (se rellenará con ARP reply) */
            ensamblar_eth_header(eth_pending, interfaz_salida->addr, zero_mac, ethertype_ip);
            memcpy(full_pkt + sizeof(sr_ethernet_hdr_t), ip_nupacket, sizeof(ip_nupacket));

            /* encolar el frame completo */
            sr_arpcache_queuereq(&sr->cache, next_hop_ip, full_pkt, full_len, interfaz_salida->name);

            /* enviar la solicitud ARP */
            sr_arp_request_send(sr, next_hop_ip, interfaz_salida->name);

            free(full_pkt);
        } else {
            /* Si no hay memoria, al menos intentar enviar ARP para resolver la MAC */
            sr_arp_request_send(sr, next_hop_ip, interfaz_salida->name);
        }

    }

    /* liberar el buffer ICMP temporal */
    if (icmp_packet) {
        free(icmp_packet);
        icmp_packet = NULL;
    }

}

void sr_handle_ip_packet(struct sr_instance *sr,
        uint8_t *packet /* lent */,
        unsigned int len,
        uint8_t *srcAddr,
        uint8_t *destAddr,
        char *interface /* lent */,
        sr_ethernet_hdr_t *eHdr) {

  /* 
  * COLOQUE ASÍ SU CÓDIGO
  * SUGERENCIAS: 
  * - Obtener el cabezal IP y direcciones 
  * - Verificar si el paquete es para una de mis interfaces o si hay una coincidencia en mi tabla de enrutamiento 
  * - Si no es para una de mis interfaces y no hay coincidencia en la tabla de enrutamiento, enviar ICMP net unreachable
  * - Sino, si es para mí, verificar si es un paquete ICMP echo request y responder con un echo reply 
  * - Sino, verificar TTL, ARP y reenviar si corresponde (puede necesitar una solicitud ARP y esperar la respuesta)
  * - No olvide imprimir los mensajes de depuración
  */

        if (!sr || !packet) { return; }

        /* Obtener el cabezal IP y direcciones */
        struct sr_ip_hdr *ip_hdr = (struct sr_ip_hdr *)(packet + sizeof(sr_ethernet_hdr_t));
        
        
        uint16_t ip_hdr_len = ip_hdr->ip_hl * 4;
        uint16_t ip_total_len = ntohs(ip_hdr->ip_len);
        uint8_t ip_protocol_tcp = 6;
        uint8_t ip_protocol_udp = 17;

        /* checkeamos q el largo esté bien */
        if (len < sizeof(sr_ethernet_hdr_t) + sizeof(sr_ip_hdr_t) || len < sizeof(sr_ethernet_hdr_t) + ip_hdr_len || ip_hdr_len < sizeof(sr_ip_hdr_t)) {
            fprintf(stderr, "IP packet too short or malformed\n");
            return;
        }

    uint16_t cksum_calc = ip_cksum(ip_hdr, ip_hdr_len);
    if (cksum_calc != ip_hdr->ip_sum) {
        fprintf(stderr, "Invalid IP checksum, dropping packet. ip_sum=%u, calc=%u\n", ntohs(ip_hdr->ip_sum), ntohs(cksum_calc));
        return;}

        /* Verificar si el paquete es para una de mis interfaces o si hay una coincidencia en mi tabla de enrutamiento  */
        struct sr_if *if_iter = sr->if_list;
        struct sr_if *dest_iface = NULL;
        while (if_iter) {
            if (if_iter->ip == ip_hdr->ip_dst) {
                dest_iface = if_iter;
                break;
            }
            if_iter = if_iter->next;
        }

        /* si el paquete es para una de mis interfaces */
        if (dest_iface) {
            /* ICMP echo request -> send echo reply */
            if (ip_hdr->ip_p == ip_protocol_icmp) {
                uint8_t *icmp_ptr = packet + sizeof(sr_ethernet_hdr_t) + ip_hdr_len;
                int icmp_len = ip_total_len - ip_hdr_len;
                if (icmp_len >= (int)sizeof(sr_icmp_hdr_t)) {
                    sr_icmp_hdr_t *icmp = (sr_icmp_hdr_t *)icmp_ptr;
                    if (icmp->icmp_type == 8) { /* echo request */
                        /* build reply packet */
                        uint8_t *reply = malloc(len);
                        if (!reply) { return; }
                        /* copy original packet and then fix headers */
                        memcpy(reply, packet, len);

                        sr_ethernet_hdr_t *eth_reply = (sr_ethernet_hdr_t *)reply;
                        /* swap ethernet addresses: src becomes dst and viceversa */
                        memcpy(eth_reply->ether_dhost, eHdr->ether_shost, ETHER_ADDR_LEN);
                        memcpy(eth_reply->ether_shost, dest_iface->addr, ETHER_ADDR_LEN);
                        eth_reply->ether_type = htons(ethertype_ip);

                        /* IP header */
                        struct sr_ip_hdr *ipr = (struct sr_ip_hdr *)(reply + sizeof(sr_ethernet_hdr_t));
                        ipr->ip_dst = ip_hdr->ip_src;
                        ipr->ip_src = dest_iface->ip;
                        ipr->ip_ttl = 64;
                        ipr->ip_sum = 0;
                        ipr->ip_sum = ip_cksum(ipr, ip_hdr_len);

                        /* ICMP header: change type to echo reply (0) and recompute checksum */
                        sr_icmp_hdr_t *icmp_r = (sr_icmp_hdr_t *)(reply + sizeof(sr_ethernet_hdr_t) + ip_hdr_len);
                        icmp_r->icmp_type = 0;
                        icmp_r->icmp_code = 0;
                        /* recompute icmp checksum over icmp_len bytes */
                        icmp_r->icmp_sum = 0;
                        icmp_r->icmp_sum = icmp_cksum(icmp_r, icmp_len);

                        print_hdrs(reply, len);
                        sr_send_packet(sr, reply, len, dest_iface->name);
                        free(reply);
                        return;
                    }
                }
            }

            /* If packet to router and TCP/UDP -> send ICMP port unreachable */
            if (ip_hdr->ip_p == ip_protocol_tcp || ip_hdr->ip_p == ip_protocol_udp) {
                /* send ICMP port unreachable back to source */
                sr_send_icmp_error_packet(3, 3, sr, ip_hdr->ip_src,  packet + sizeof(sr_ethernet_hdr_t));
                return;
            }

            /* For other protocols destined to router, just drop */
            return;
        }

        /* o si hay una coincidencia en mi tabla de enrutamiento -> reenvío */

        /* TTL handling */
        if (ip_hdr->ip_ttl <= 1) {
            /* send ICMP time exceeded to original sender */
            sr_send_icmp_error_packet(11, 0, sr, ip_hdr->ip_src,  packet + sizeof(sr_ethernet_hdr_t));
            return;
        }

        /* decrement TTL and recompute checksum */
        ip_hdr->ip_ttl -= 1;
        ip_hdr->ip_sum = 0;
        ip_hdr->ip_sum = ip_cksum(ip_hdr, ip_hdr_len);

        /* longest prefix match in routing table */
        struct sr_rt *rt_entry = sr_prefijo_mas_largo(sr, ip_hdr->ip_dst);
        if (!rt_entry) {
            /* no route -> destination net unreachable */
            sr_send_icmp_error_packet(3, 0, sr, ip_hdr->ip_src, packet + sizeof(sr_ethernet_hdr_t));
            return;
        } else {
    fprintf(stderr,"CHOSE ROUTE: dest=%s mask=%s gw=%s iface=%s\n",
            inet_ntoa(rt_entry->dest), inet_ntoa(rt_entry->mask),
            inet_ntoa(rt_entry->gw), rt_entry->interface);
    }

        /* determine next hop */
        uint32_t next_hop = (rt_entry->gw.s_addr != 0) ? rt_entry->gw.s_addr : ip_hdr->ip_dst;

        /* get outgoing interface */
        struct sr_if *out_iface = sr_get_interface(sr, rt_entry->interface);
        if (!out_iface) {
            fprintf(stderr, "No outgoing interface found for route\n");
            return;
        }

        /* lookup ARP for next hop */
        struct sr_arpentry *entry = sr_arpcache_lookup(&sr->cache, next_hop);
        if (entry) {
            /* build ethernet frame: copy packet then update eth header */
            uint8_t *fwd_packet = malloc(len);
            if (!fwd_packet) { free(entry); return; }
            memcpy(fwd_packet, packet, len);

            sr_ethernet_hdr_t *eth_fwd = (sr_ethernet_hdr_t *)fwd_packet;
            ensamblar_eth_header(eth_fwd, out_iface->addr, entry->mac, ethertype_ip);

            print_hdrs(fwd_packet, len);
            sr_send_packet(sr, fwd_packet, len, out_iface->name);

            free(fwd_packet);
            free(entry);
        } else {
            /* queue packet waiting for ARP reply */
            sr_arpcache_queuereq(&sr->cache, next_hop, packet, len, out_iface->name);
            /* trigger an ARP request immediately */
            sr_arp_request_send(sr, next_hop, out_iface->name);
        }

}

/* Gestiona la llegada de un paquete ARP*/
void sr_handle_arp_packet(struct sr_instance *sr,
        uint8_t *packet /* lent */,
        unsigned int len,
        uint8_t *srcAddr,
        uint8_t *destAddr,
        char *interface /* lent */,
        sr_ethernet_hdr_t *eHdr) {
/* COLOQUE SU CÓDIGO AQUÍ
  
  SUGERENCIAS:
  - Verifique si se trata de un ARP request o ARP reply 
  - Si es una ARP request, antes de responder verifique si el mensaje consulta por la dirección MAC asociada a una dirección IP configurada en una interfaz del router
  - Si es una ARP reply, agregue el mapeo MAC->IP del emisor a la caché ARP y envíe los paquetes que hayan estado esperando por el ARP reply
  
  */

    if (len < sizeof(sr_ethernet_hdr_t) + sizeof(sr_arp_hdr_t)) {
        fprintf(stderr, "ARP packet too short\n");
        return;
    }

    sr_arp_hdr_t *arp_hdr = (sr_arp_hdr_t *)(packet + sizeof(sr_ethernet_hdr_t));

    printf("*** -> It is an ARP packet. Print ARP header.\n");
    print_hdr_arp(packet + sizeof(sr_ethernet_hdr_t));

    /* Si es un ARP request */
    if (ntohs(arp_hdr->ar_op) == arp_op_request) {
        struct sr_if *iface_iter = sr->if_list;
        while (iface_iter) {
            if (ntohl(arp_hdr->ar_tip) == ntohl(iface_iter->ip)) {
                /* ARP request dirigido a esta interfaz, armar reply */
                uint8_t *reply = malloc(sizeof(sr_ethernet_hdr_t) + sizeof(sr_arp_hdr_t));
                if (!reply) return;

                sr_ethernet_hdr_t *replyEthHdr = (sr_ethernet_hdr_t *)reply;
                sr_arp_hdr_t *replyArpHdr = (sr_arp_hdr_t *)(reply + sizeof(sr_ethernet_hdr_t));

                /* Construir Ethernet header */
                ensamblar_eth_header(replyEthHdr, iface_iter->addr, arp_hdr->ar_sha, ethertype_arp);

                /* Construir ARP header */
                replyArpHdr->ar_hrd = htons(arp_hrd_ethernet);
                replyArpHdr->ar_pro = htons(ethertype_ip);
                replyArpHdr->ar_hln = ETHER_ADDR_LEN;
                replyArpHdr->ar_pln = 4;
                replyArpHdr->ar_op = htons(arp_op_reply);
                memcpy(replyArpHdr->ar_sha, iface_iter->addr, ETHER_ADDR_LEN);
                replyArpHdr->ar_sip = iface_iter->ip;
                memcpy(replyArpHdr->ar_tha, arp_hdr->ar_sha, ETHER_ADDR_LEN);
                replyArpHdr->ar_tip = arp_hdr->ar_sip;

                /* Enviar reply por la misma interfaz que llegó el request */
                sr_send_packet(sr, reply, sizeof(sr_ethernet_hdr_t) + sizeof(sr_arp_hdr_t), interface);
                free(reply);

                break;  /* ya respondimos, no seguimos iterando */
            }
            iface_iter = iface_iter->next;
        }
    }
    /* Si es un ARP reply */
    else if (ntohs(arp_hdr->ar_op) == arp_op_reply) {
        /* Insertar el mapeo en la caché y obtener la solicitud (si existe)
           sr_arpcache_insert devuelve la sr_arpreq asociada si había paquetes
           pendientes para esta IP. */
        struct sr_arpreq *req = sr_arpcache_insert(&(sr->cache), arp_hdr->ar_sha, arp_hdr->ar_sip);
        if (req != NULL) {
            /* Obtener la interfaz por la cual llegó el ARP para confirmar pendientes */
            struct sr_if *iface = sr_get_interface(sr, interface);
            if (iface) {
                sr_arp_reply_send_pending_packets(sr, req, arp_hdr->ar_sha, iface->addr, iface);
            } 
            /* Finalmente destruir la solicitud (libera la lista de paquetes)
               sr_arp_reply_send_pending_packets ya hizo send de copias. */
            sr_arpreq_destroy(&(sr->cache), req);
        }
    }
}

 
/* 
* ***** A partir de aquí no debería tener que modificar nada ****
*/

/* Envía todos los paquetes IP pendientes de una solicitud ARP */
void sr_arp_reply_send_pending_packets(struct sr_instance *sr,
                                        struct sr_arpreq *arpReq,
                                        uint8_t *dhost,
                                        uint8_t *shost,
                                        struct sr_if *iface) {

  struct sr_packet *currPacket = arpReq->packets;
  sr_ethernet_hdr_t *ethHdr;
  uint8_t *copyPacket;

  while (currPacket != NULL) {
     ethHdr = (sr_ethernet_hdr_t *) currPacket->buf;
     memcpy(ethHdr->ether_shost, shost, sizeof(uint8_t) * ETHER_ADDR_LEN);
     memcpy(ethHdr->ether_dhost, dhost, sizeof(uint8_t) * ETHER_ADDR_LEN);

     copyPacket = malloc(sizeof(uint8_t) * currPacket->len);
     memcpy(copyPacket, ethHdr, sizeof(uint8_t) * currPacket->len);

     print_hdrs(copyPacket, currPacket->len);
     sr_send_packet(sr, copyPacket, currPacket->len, iface->name);
     free(copyPacket);
     currPacket = currPacket->next;
  }
}

/*---------------------------------------------------------------------
 * Method: sr_handlepacket(uint8_t* p,char* interface)
 * Scope:  Global
 *
 * This method is called each time the router receives a packet on the
 * interface.  The packet buffer, the packet length and the receiving
 * interface are passed in as parameters. The packet is complete with
 * ethernet headers.
 *
 * Note: Both the packet buffer and the character's memory are handled
 * by sr_vns_comm.c that means do NOT delete either.  Make a copy of the
 * packet instead if you intend to keep it around beyond the scope of
 * the method call.
 *
 *---------------------------------------------------------------------*/

void sr_handlepacket(struct sr_instance* sr,
        uint8_t * packet/* lent */,
        unsigned int len,
        char* interface/* lent */)
{
  assert(sr);
  assert(packet);
  assert(interface);

  printf("*** -> Received packet of length %d \n",len);

  /* Obtengo direcciones MAC origen y destino */
  sr_ethernet_hdr_t *eHdr = (sr_ethernet_hdr_t *) packet;
  uint8_t *destAddr = malloc(sizeof(uint8_t) * ETHER_ADDR_LEN);
  uint8_t *srcAddr = malloc(sizeof(uint8_t) * ETHER_ADDR_LEN);
  memcpy(destAddr, eHdr->ether_dhost, sizeof(uint8_t) * ETHER_ADDR_LEN);
  memcpy(srcAddr, eHdr->ether_shost, sizeof(uint8_t) * ETHER_ADDR_LEN);
  uint16_t pktType = ntohs(eHdr->ether_type);

  if (is_packet_valid(packet, len)) {
    if (pktType == ethertype_arp) {
      sr_handle_arp_packet(sr, packet, len, srcAddr, destAddr, interface, eHdr);
    } else if (pktType == ethertype_ip) {
      sr_handle_ip_packet(sr, packet, len, srcAddr, destAddr, interface, eHdr);
    }
  }

}/* end sr_ForwardPacket */



    /* Funciones Auxiliares para envios */


    
    /* apartir de una ip encuentra su prefijo mas largo correspondiente a una entrada de la tabla para luego poder identificar la interfaz de salida
     asociada */
struct sr_rt* sr_prefijo_mas_largo(struct sr_instance* sr, uint32_t ip)
{
    struct sr_rt* rt_iterador = sr->routing_table;
    struct sr_rt* mejor_entrada = NULL;
    uint32_t mask_maslargo = 0;

    while (rt_iterador != NULL) {
        uint32_t masked_ip = ip & rt_iterador->mask.s_addr;
        uint32_t masked_dest = rt_iterador->dest.s_addr & rt_iterador->mask.s_addr;

        if (masked_ip == masked_dest) {
            uint32_t mask_len = ntohl(rt_iterador->mask.s_addr);
            if (mask_len > mask_maslargo) {
                mask_maslargo = mask_len;
                mejor_entrada = rt_iterador;
            }
        }
        rt_iterador = rt_iterador->next;
    }
    return mejor_entrada;
}

   /* construye el cabezal ip*/

void ensamblar_ip_header(struct sr_ip_hdr *ip_hdr,
                     uint32_t src_ip,
                     uint32_t dst_ip,
                     uint16_t total_len,
                     uint8_t protocol)
{
    ip_hdr->ip_v = 4;
    ip_hdr->ip_hl = 5;
    ip_hdr->ip_tos = 0;
    ip_hdr->ip_len = htons(total_len);
    ip_hdr->ip_id = 0;
    ip_hdr->ip_off = 0;
    ip_hdr->ip_ttl = 64;
    ip_hdr->ip_p = protocol;
    ip_hdr->ip_src = src_ip;
    ip_hdr->ip_dst = dst_ip;
    ip_hdr->ip_sum = 0;
    ip_hdr->ip_sum = ip_cksum(ip_hdr, sizeof(sr_ip_hdr_t));
}

/* construye el cabezal ethernet*/
void ensamblar_eth_header(struct sr_ethernet_hdr *eth_hdr,
                      uint8_t *src_mac,
                      uint8_t *dst_mac,
                      uint16_t ethertype)
{
    memcpy(eth_hdr->ether_shost, src_mac, ETHER_ADDR_LEN);
    memcpy(eth_hdr->ether_dhost, dst_mac, ETHER_ADDR_LEN);
    eth_hdr->ether_type = htons(ethertype);
}
