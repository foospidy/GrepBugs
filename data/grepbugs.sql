
create table metadata (          -- http://cloc.sourceforge.net v 1.56
                timestamp text,    
                Project   text,    
                elapsed_s real);   
create table t        (
                Project   text   ,  
                Language  text   ,  
                File      text   ,  
                nBlank    integer,  
                nComment  integer,  
                nCode     integer,  
                nScaled   real   ); 
begin transaction;
insert into metadata values('2014-07-12 11:20:31', 'src/mwielgoszewski/www.tssci-security.com', 1.000000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'make', 'src/mwielgoszewski/www.tssci-security.com/Makefile', 14, 9, 35, 87.500000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/error.html', 0, 0, 8, 15.200000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/layout.html', 6, 0, 37, 70.300000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/blog/_entry.html', 1, 0, 13, 24.700000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/tag.html', 0, 0, 10, 19.000000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/tagcloud.html', 0, 0, 16, 30.400000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/page.html', 0, 0, 1, 1.900000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/base.html', 2, 0, 12, 22.800000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/blog/archive.html', 0, 0, 15, 28.500000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'Javascript', 'src/mwielgoszewski/www.tssci-security.com/static/js/functions.js', 7, 0, 30, 44.400000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/blog/month_archive.html', 0, 0, 10, 19.000000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/sidebar.html', 1, 0, 10, 19.000000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'YAML', 'src/mwielgoszewski/www.tssci-security.com/config.yml', 0, 1, 27, 24.300000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/blog/index.html', 2, 0, 23, 43.700000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/blog/year_archive.html', 0, 0, 12, 22.800000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/post.html', 0, 0, 15, 28.500000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'CSS', 'src/mwielgoszewski/www.tssci-security.com/static/css/style.css', 48, 1, 209, 209.000000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/search.html', 0, 0, 7, 13.300000);
insert into t values('src/mwielgoszewski/www.tssci-security.com', 'HTML', 'src/mwielgoszewski/www.tssci-security.com/_templates/_pagination.html', 0, 0, 13, 24.700000);
commit;
