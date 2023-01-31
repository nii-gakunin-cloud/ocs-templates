#!/usr/bin/env python3
import os
import sys
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from pathlib import Path

NS = "urn:mace:shibboleth:3.0:native:sp:config"
NS_MAP = {"c": NS}


def update_entity_id(xml, hostname):
    node = xml.find("c:ApplicationDefaults[@entityID]", NS_MAP)
    if node is not None:
        node.set("entityID", f"https://{hostname}/shibboleth-sp")


def update_ds_server(xml, samlds):
    node = xml.find('.//c:SessionInitiator[@type="SAMLDS"]', NS_MAP)
    if node is not None:
        node.set("URL", samlds)
        return

    parent = xml.find('.//c:Sessions/c:SessionInitiator[@type="Chaining"]', NS_MAP)
    if parent is not None:
        ET.SubElement(
            parent,
            "SessionInitiator",
            attrib={
                "type": "SAMLDS",
                "URL": samlds,
            },
        )
        return

    parent = xml.find(".//c:Sessions", NS_MAP)
    if parent is None:
        parent = ET.Element(
            "Sessions",
            attrib={
                "lifetime": "28800",
                "timeout": "3600",
                "relayState": "ss:mem",
                "checkAddress": "false",
                "handlerSSL": "true",
                "cookieProps": "https",
                "redirectLimit": "exact",
            },
        )
        xml.find("c:ApplicationDefaults[@entityID]", NS_MAP).insert(0, parent)
    node = ET.Element(
        "SessionInitiator",
        attrib={
            "type": "Chaining",
            "Location": "/DS",
            "isDefault": "true",
            "id": "DS",
        },
    )
    parent.append(node)
    attrib_list = [
        {
            "type": "SAML2",
            "template": "bindingTemplate.html",
        },
        {
            "type": "Shib1",
        },
        {
            "type": "SAMLDS",
            "URL": samlds,
        },
    ]
    for attrib in attrib_list:
        ET.SubElement(node, "SessionInitiator", attrib=attrib)


def update_metadata(xml, metadata_url):
    node = xml.find('.//c:MetadataProvider[@type="XML"][@url]', NS_MAP)
    if node is not None:
        node.set("url", metadata_url)
        return

    parent = xml.find(".//c:ApplicationDefaults", NS_MAP)
    mp = ET.Element(
        "MetadataProvider",
        attrib={
            "type": "XML",
            "validate": "true",
            "url": metadata_url,
            "backingFilePath": "federation-metadata.xml",
            "maxRefreshDelay": "7200",
        },
    )
    parent.append(mp)
    mf_attribs = [
        {
            "type": "RequireValidUntil",
            "maxValidityInterval": "1296000",
        },
        {
            "type": "Signature",
            "certificate": "/etc/shibboleth/cert/gakunin-signer.cer",
            "verifyBackup": "false",
        },
    ]
    for attrib in mf_attribs:
        mp.append(ET.Element("MetadataFilter", attrib=attrib))

    df = ET.Element(
        "DiscoveryFilter",
        attrib={
            "type": "Exclude",
            "matcher": "EntityAttributes",
            "trimTags": "true",
            "attributeName": "http://macedir.org/entity-category",
            "attributeNameFormat": "urn:oasis:names:tc:SAML:2.0:attrname-format:uri",
            "attributeValue": "http://refeds.org/category/hide-from-discovery",
        },
    )
    mp.append(df)

    tp_attribs = [
        [
            {
                "provider": "CURL",
                "option": "64",
            },
            "1",
        ],
        [
            {
                "provider": "CURL",
                "option": "81",
            },
            "2",
        ],
        [
            {
                "provider": "CURL",
                "option": "10065",
            },
            "/etc/pki/tls/certs/ca-bundle.crt",
        ],
    ]
    for attrib, text in tp_attribs:
        node = ET.Element("TransportOption", attrib=attrib)
        node.text = text
        mp.append(node)


def update_credential_resolver(xml):
    nodes = xml.findall('.//c:CredentialResolver[@type="File"]', NS_MAP)
    for node in nodes:
        node.set("key", "cert/server.key")
        node.set("certificate", "cert/server.crt")


def show_xml(tree, output):
    ET.register_namespace("", NS)
    ET.indent(tree, space=(" " * 4))
    tree.write(output if output is not None else sys.stdout.buffer)


def update_shib2(xml, hostname, samlds, metadata_url, idp_entity_id, idp_metadata):
    update_entity_id(xml, hostname)
    if samlds is not None:
        update_ds_server(xml, samlds)
    if metadata_url is not None:
        update_metadata(xml, metadata_url)
    update_credential_resolver(xml)
    if idp_entity_id is not None:
        update_sso(xml, idp_entity_id)
        if samlds is None:
            comment_out_session_initiator(xml)
    if idp_metadata is not None:
        update_metadata_provider(xml, idp_metadata)
        if metadata_url is None:
            comment_out_gakunin_metadata_provider(xml)


def to_comment(node):
    txt = ET.tostring(node, encoding="unicode")
    return ET.Comment(f" {txt.strip()} ")


def comment_out_nodes(xml, xpath):
    targets = xml.findall(xpath, NS_MAP)
    parent = xml.find(f"{xpath}/..", NS_MAP)
    if parent is not None:
        children = [x for x in parent]
        for node in children:
            parent.remove(node)
        for node in children:
            parent.append(node if node not in targets else to_comment(node))


def comment_out_metadata_generator(xml):
    comment_out_nodes(xml, './/c:Sessions/c:Handler[@type="MetadataGenerator"]')


def update_sso(xml, idp_entity_id):
    node = xml.find(".//c:Sessions/c:SSO", NS_MAP)
    if node is not None:
        node.set("entityID", idp_entity_id)


def update_metadata_provider(xml, idp_metadata):
    target = xml.find(
        './/c:ApplicationDefaults/MetadataProvider[@type="XML"][@path]', NS_MAP
    )
    if target is not None:
        target.set("path", idp_metadata)
    else:
        parent = xml.find(".//c:ApplicationDefaults", NS_MAP)
        attrib = {
            "type": "XML",
            "path": str(idp_metadata),
            "validate": "true",
        }
        parent.append(ET.Element("MetadataProvider", attrib=attrib))


def comment_out_session_initiator(xml):
    comment_out_nodes(xml, './/c:Sessions/c:SessionInitiator[@type="Chaining"]')


def comment_out_gakunin_metadata_provider(xml):
    comment_out_nodes(xml, ".//c:ApplicationDefaults/c:MetadataProvider[@url]")


def setup_shibbleth2_xml(
    hostname,
    conf,
    output=None,
    samlds=None,
    metadata_url=None,
    idp_entity_id=None,
    idp_metadata=None,
):
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(conf, parser)
    root = tree.getroot()
    update_shib2(root, hostname, samlds, metadata_url, idp_entity_id, idp_metadata)
    comment_out_metadata_generator(root)
    show_xml(tree, output)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", default="/etc/shibboleth/shibboleth2.xml")
    parser.add_argument("-o", "--output")
    parser.add_argument(
        "-s",
        "--sp-hostname",
        dest="hostname",
        required=("SERVER_NAME" not in os.environ),
    )
    parser.add_argument("--gakunin-ds", dest="samlds")
    parser.add_argument("--gakunin-metadata", dest="metadata_url")
    parser.add_argument("--idp-entity-id")
    parser.add_argument("--idp-metadata")

    args = parser.parse_args()
    if args.hostname is None:
        args.hostname = os.environ["SERVER_NAME"]
    if args.samlds is None:
        args.samlds = os.environ.get("GAKUNIN_DS")
    if args.metadata_url is None:
        args.metadata_url = os.environ.get("GAKUNIN_METADATA")
    if args.idp_entity_id is None:
        args.idp_entity_id = os.environ.get("IDP_ENTITY_ID")
    if args.idp_metadata is None:
        args.idp_metadata = os.environ.get("IDP_METADATA")
    return args


def main():
    args = parse_args()
    output = (
        Path(args.output)
        if args.output is not None and args.output.strip() != "-"
        else None
    )
    setup_shibbleth2_xml(
        args.hostname,
        Path(args.input),
        output,
        args.samlds,
        args.metadata_url,
        args.idp_entity_id,
        args.idp_metadata,
    )


if __name__ == "__main__":
    main()
