-- MySQL dump 10.13  Distrib 5.1.36, for Win64 (unknown)
--
-- Host: localhost    Database: Bucket
-- ------------------------------------------------------
-- Server version	5.1.36-community

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `pail_facts`
--

DROP TABLE IF EXISTS `pail_facts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pail_facts` (
  `name` varchar(50) NOT NULL,
  `method` varchar(20) NOT NULL,
  `response` varchar(200) NOT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `protected` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=43 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pail_facts`
--

LOCK TABLES `pail_facts` WRITE;
/*!40000 ALTER TABLE `pail_facts` DISABLE KEYS */;
INSERT INTO `pail_facts` VALUES ('what are you carrying?','reply','I am carrying $inventory',1,0),('giveback','action','gives $giveitem.particle $giveitem back to $giveitem.owner',2,0),('giveback','action','hands $giveitem.particle $giveitem back to $giveitem.owner',3,0),('giveback','action','throws $giveitem.particle $giveitem at $someone',4,0),('nothanks','reply','No thanks $who, I already have one',5,0),('nothanks','reply','No thanks $who, I already have $this.particle $this',6,0),('maxitems','action','takes $this.particle $this and drops $agiveitem',7,0),('maxitems','action','takes $this.particle $this and gives $who $agiveitem in return',8,0),('maxitems','action','takes $this.particle $this and gives its $giveitem back to $giveitem.owner',9,0),('takeitem','action','now contains $inventory',10,0),('takeitem','action','now has $inventory in it',11,0),('dontknow','reply','I\'m sorry $who, I\'m afraid I can\'t do that',12,0),('dontknow','action','explodes',13,0),('dontknow','action','gives $who a suplex',14,0),('dontknow','reply','Error: syntax error in line 1',15,0);
/*!40000 ALTER TABLE `pail_facts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pail_items`
--

DROP TABLE IF EXISTS `pail_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pail_items` (
  `name` varchar(50) NOT NULL,
  `owner` varchar(20) NOT NULL,
  `particle` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pail_items`
--

LOCK TABLES `pail_items` WRITE;
/*!40000 ALTER TABLE `pail_items` DISABLE KEYS */;
INSERT INTO `pail_items` VALUES ('mallet','Will','a'),('knife','Will','a'),('vodka','Will','some'),('tequila','Will','some'),('piece of string','Will','a'),('the test','Will',NULL),('rusty nail','Will','a'),('book','Will','a');
/*!40000 ALTER TABLE `pail_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pail_vars`
--

DROP TABLE IF EXISTS `pail_vars`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `pail_vars` (
  `name` varchar(50) NOT NULL,
  `value` varchar(50) NOT NULL,
  `id` int(20) unsigned NOT NULL AUTO_INCREMENT,
  `protected` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pail_vars`
--

LOCK TABLES `pail_vars` WRITE;
/*!40000 ALTER TABLE `pail_vars` DISABLE KEYS */;
INSERT INTO `pail_vars` VALUES ('aitem','$item.particle $item',1,0),('agiveitem','$giveitem.particle $giveitem',2,0);
/*!40000 ALTER TABLE `pail_vars` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-11-11 13:36:37
