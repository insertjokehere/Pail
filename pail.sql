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
-- Table structure for table `bucket_facts`
--

DROP TABLE IF EXISTS `bucket_facts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bucket_facts` (
  `name` varchar(50) NOT NULL,
  `method` varchar(20) NOT NULL,
  `response` varchar(200) NOT NULL,
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `protected` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bucket_facts`
--

LOCK TABLES `bucket_facts` WRITE;
/*!40000 ALTER TABLE `bucket_facts` DISABLE KEYS */;
--INSERT INTO `bucket_facts` VALUES ('jonathan','is','awesome',13,0),('o/','reply','o/\\o',15,0),('who is cool?','reply','you are $who',16,0),('say hi','reply','Hi, $someone!',18,0),('speak','action','jumps up and down',19,0);
/*!40000 ALTER TABLE `bucket_facts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bucket_vars`
--

DROP TABLE IF EXISTS `bucket_vars`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bucket_vars` (
  `name` varchar(50) NOT NULL,
  `value` varchar(20) NOT NULL,
  `id` int(20) unsigned NOT NULL AUTO_INCREMENT,
  `protected` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bucket_vars`
--

LOCK TABLES `bucket_vars` WRITE;
/*!40000 ALTER TABLE `bucket_vars` DISABLE KEYS */;
--INSERT INTO `bucket_vars` VALUES ('test','abcd',3,0),('test','foo',4,0);
/*!40000 ALTER TABLE `bucket_vars` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2011-11-07 17:21:56
