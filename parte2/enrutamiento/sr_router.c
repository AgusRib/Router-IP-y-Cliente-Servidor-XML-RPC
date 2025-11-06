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
#include "sr_rip.h"

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

    /* Inicializa el subsistema RIP */
    sr_rip_init(sr);

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

  /* COLOQUE AQUÍ SU CÓDIGO*/

} /* -- sr_send_icmp_error_packet -- */

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
  * - Si es para mí, verificar si es un paquete ICMP echo request y responder con un echo reply
  * - Si es para mí o a la IP multicast de RIP, verificar si contiene un datagrama UDP y es destinado al puerto RIP, en ese caso pasarlo al subsistema RIP.
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

  /* Imprimo el cabezal ARP */
  printf("*** -> It is an ARP packet. Print ARP header.\n");
  print_hdr_arp(packet + sizeof(sr_ethernet_hdr_t));

  /* COLOQUE SU CÓDIGO AQUÍ

  SUGERENCIAS:
  - Verifique si se trata de un ARP request o ARP reply
  - Si es una ARP request, antes de responder verifique si el mensaje consulta por la dirección MAC asociada a una dirección IP configurada en una interfaz del router
  - Si es una ARP reply, agregue el mapeo MAC->IP del emisor a la caché ARP y envíe los paquetes que hayan estado esperando por el ARP reply

  */
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