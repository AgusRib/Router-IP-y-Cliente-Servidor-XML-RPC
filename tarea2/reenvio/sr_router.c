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
      print "$$$ -> ERROR no se encontro entrada en la tabla de reenvio.\n";
        return;
    }

    struct sr_if *interfaz_salida = sr_get_interface(sr, rt_entry->interface);
    if (!interfaz_salida) {
      print "$$$ -> ERROR no se encontro la interfaz de salida.\n";
        return;
    }


    uint32_t next_hop_ip = (rt_entry->gw.s_addr != 0) ? rt_entry->gw.s_addr : ipDst;

  

    if (type == 3) {
          uint8_t icmp_packet[sizeof(sr_icmp_t3_hdr_t)];
          uint16_t icmp_len;
        sr_icmp_t3_hdr_t *icmp3 = (sr_icmp_t3_hdr_t *)icmp_packet;
        icmp3->icmp_type = type;
        icmp3->icmp_code = code;
        icmp3->unused = 0;
        icmp3->next_mtu = 0;
        memcpy(icmp3->data, ipPacket, ICMP_DATA_SIZE);
        icmp3->icmp_sum = 0;
        icmp3->icmp_sum = icmp3_cksum((uint16_t *)icmp3, sizeof(sr_icmp_t3_hdr_t));
        icmp_len = sizeof(sr_icmp_t3_hdr_t);
    } else if (type == 11) {
        uint8_t icmp_packet[sizeof(sr_icmp_hdr_t) + ICMP_DATA_SIZE];
        uint16_t icmp_len;
        sr_icmp_hdr_t *icmp11 = (sr_icmp_hdr_t *)icmp_packet;
        icmp11->icmp_type = type;
        icmp11->icmp_code = code;
        icmp11->icmp_sum = 0;
        memcpy(icmp_packet + sizeof(sr_icmp_hdr_t), ipPacket, ICMP_DATA_SIZE);
        icmp11->icmp_sum = icmp_cksum((uint16_t *)icmp_packet,
                                 sizeof(sr_icmp_hdr_t) + ICMP_DATA_SIZE);
        icmp_len = sizeof(sr_icmp_hdr_t) + ICMP_DATA_SIZE;
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
        sr_arpcache_queuereq(&sr->cache, next_hop_ip,
                             ip_nupacket, sizeof(ip_nupacket), interfaz_salida->name);
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

    if (len < sizeof(sr_ethernet_hdr_t) + sizeof(sr_arp_hdr_t)) {
        fprintf(stderr, "ARP packet too short\n");
        return;
    }

    sr_arp_hdr_t *arp_hdr = (sr_arp_hdr_t *)(packet + sizeof(sr_ethernet_hdr_t));
    struct sr_if *iface = sr_get_interface(sr, interface);

    /* Si es un ARP request */
    if (ntohs(arp_hdr->ar_op) == arp_op_request) {
        if (arp_hdr->ar_tip == iface->ip) {
            uint8_t *reply = malloc(sizeof(sr_ethernet_hdr_t) + sizeof(sr_arp_hdr_t));
            sr_ethernet_hdr_t *replyEthHdr = (sr_ethernet_hdr_t *)reply;
            sr_arp_hdr_t *replyArpHdr = (sr_arp_hdr_t *)(reply + sizeof(sr_ethernet_hdr_t));

            ensamblar_eth_header(replyEthHdr, arp_hdr->ar_sha, iface->addr, ethertype_arp);

            replyArpHdr->ar_hrd = htons(arp_hrd_ethernet);
            replyArpHdr->ar_pro = htons(ethertype_ip);
            replyArpHdr->ar_hln = ETHER_ADDR_LEN;
            replyArpHdr->ar_pln = 4;
            replyArpHdr->ar_op = htons(arp_op_reply);
            memcpy(replyArpHdr->ar_sha, iface->addr, ETHER_ADDR_LEN);
            replyArpHdr->ar_sip = iface->ip;
            memcpy(replyArpHdr->ar_tha, arp_hdr->ar_sha, ETHER_ADDR_LEN);
            replyArpHdr->ar_tip = arp_hdr->ar_sip;

            sr_send_packet(sr, reply, sizeof(sr_ethernet_hdr_t) + sizeof(sr_arp_hdr_t), interface);
            free(reply);
        }
    }
    /* Si es un ARP reply */
    else if (ntohs(arp_hdr->ar_op) == arp_op_reply) {
        struct sr_arpreq *req = sr_arpcache_insert(&(sr->cache), arp_hdr->ar_sha, arp_hdr->ar_sip);
        if (req != NULL) {
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
    ip_hdr->ip_sum = ip_cksum((uint16_t *)ip_hdr, sizeof(sr_ip_hdr_t));
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
